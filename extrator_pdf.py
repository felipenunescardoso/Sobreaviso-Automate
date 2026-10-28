from datetime import date, datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from inicio import conn


MESES_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

DIAS_SEMANA_PT = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}


def calcular_competencia(data_referencia=None):
    """
    A competência do Sobreaviso sempre é:
        dia 11 do mês anterior até dia 10 do mês da referência.

    Exemplo:
        referência: 14/08/2026
        início:     11/07/2026
        fim:        10/08/2026
    """

    if data_referencia is None:
        data_referencia = date.today()

    if isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()

    primeiro_dia_mes = data_referencia.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes - timedelta(days=1)

    competencia_inicio = date(
        ultimo_dia_mes_anterior.year,
        ultimo_dia_mes_anterior.month,
        11,
    )

    competencia_fim = date(
        data_referencia.year,
        data_referencia.month,
        10,
    )

    return competencia_inicio, competencia_fim


def buscar_lancamentos(id_usuario, data_referencia=None):

    competencia_inicio, competencia_fim = calcular_competencia(
        data_referencia
    )

    fim_exclusivo = competencia_fim + timedelta(days=1)

    sql = """
        SELECT
            u.id_usuario,
            u.nome,
            u.chapa,
            d.nome_departamento,
            e.id_escala,
            ec.id_escala_competencia,
            l.id_lancamento,
            l.tipo,
            l.data_hora_inicio,
            l.data_hora_fim,
            l.motivo
        FROM sobreaviso.lancamentos l

        JOIN sobreaviso.escala_competencias ec
            ON ec.id_escala_competencia =
               l.id_escala_competencia

        JOIN sobreaviso.escalas e
            ON e.id_escala = ec.id_escala

        JOIN sobreaviso.usuarios u
            ON u.id_usuario = e.id_usuario

        JOIN sobreaviso.departamentos d
            ON d.id_departamento = u.id_departamento

        WHERE u.id_usuario = %s
          AND l.data_hora_inicio >= %s
          AND l.data_hora_inicio < %s

        ORDER BY
            l.data_hora_inicio,
            l.id_lancamento;
    """

    with conn.cursor() as cur:

        cur.execute(
            sql,
            (
                id_usuario,
                competencia_inicio,
                fim_exclusivo
            )
        )

        colunas = [
            coluna.name
            for coluna in cur.description
        ]

        linhas = cur.fetchall()

        print("USUARIO:", id_usuario)
        print("INICIO:", competencia_inicio)
        print("FIM:", fim_exclusivo)
        print("LINHAS ENCONTRADAS:", len(linhas))

        registros = [
            dict(zip(colunas, linha))
            for linha in linhas
        ]

    return competencia_inicio, competencia_fim, registros


def buscar_usuario(id_usuario):
    sql = """
        SELECT
            u.id_usuario,
            u.nome,
            u.chapa,
            u.email,
            d.nome_departamento,
            u.id_empresa,
            e.nome_empresa,
            e.banco_de_horas,
            u.id_cidade,
            u.uf
        FROM sobreaviso.usuarios u
        INNER JOIN sobreaviso.departamentos d
            ON d.id_departamento = u.id_departamento
        INNER JOIN sobreaviso.empresas e
            ON e.id_empresa = u.id_empresa
        WHERE u.id_usuario = %s
          AND u.ativo = TRUE;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (id_usuario,))
        linha = cur.fetchone()

        if not linha:
            return None

        colunas = [coluna.name for coluna in cur.description]
        return dict(zip(colunas, linha))


def formatar_duracao(inicio, fim):
    total_segundos = max(0, int((fim - inicio).total_seconds()))
    horas, resto = divmod(total_segundos, 3600)
    minutos = resto // 60
    return f"{horas:02d}:{minutos:02d}"


def formatar_segundos(total_segundos):
    total_segundos = max(0, int(total_segundos))
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    return f"{horas:02d}:{minutos:02d}"


def eh_feriado(data_referencia, uf=None, id_cidade=None):
    """
    Considera feriado:
      - nacional: uf e cidade nulos;
      - estadual: mesma UF e cidade nula;
      - municipal: mesma cidade.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS
            (
                SELECT 1
                FROM sobreaviso.feriados f
                WHERE f.data_feriado = %s
                  AND f.ativo = TRUE
                  AND
                  (
                        (f.uf IS NULL AND f.id_cidade IS NULL)
                        OR (f.uf = %s AND f.id_cidade IS NULL)
                        OR (f.id_cidade = %s)
                  )
            );
        """, (
            data_referencia,
            uf.upper() if uf else None,
            id_cidade
        ))

        return bool(cur.fetchone()[0])


def calcular_banco_horas(registros, usuario):
    """
    Classifica somente ACIONAMENTOS.

    Regra:
      - sábado/domingo: 100% horas a pagar;
      - feriado: 100% horas a pagar;
      - segunda a sexta, 00:00-07:59: 100% horas a pagar;
      - segunda a sexta, 18:01-23:59:
          até 2h acumuladas por dia -> banco de horas;
          excedente diário -> horas a pagar.

    Retorna segundos de banco e segundos a pagar.
    """
    if not usuario.get("banco_de_horas"):
        return 0, 0

    id_cidade = usuario.get("id_cidade")
    uf = usuario.get("uf")

    limite_banco_dia = 2 * 60 * 60
    banco_por_dia = {}

    segundos_banco = 0
    segundos_pagar = 0

    acionamentos = [
        r for r in registros
        if r["tipo"] == "ACIONAMENTO"
    ]

    acionamentos.sort(
        key=lambda r: (
            r["data_hora_inicio"],
            r["id_lancamento"]
        )
    )

    for registro in acionamentos:
        inicio = registro["data_hora_inicio"]
        fim = registro["data_hora_fim"]

        if fim <= inicio:
            continue

        dia = inicio.date()
        total_segundos = int((fim - inicio).total_seconds())

        # Fim de semana ou feriado: tudo a pagar.
        if inicio.weekday() >= 5 or eh_feriado(dia, uf, id_cidade):
            segundos_pagar += total_segundos
            continue

        # Em dia útil, apenas a faixa noturna 18:01-23:59
        # pode compor banco de horas.
        inicio_banco = inicio.replace(
            hour=18,
            minute=1,
            second=0,
            microsecond=0
        )

        fim_banco = inicio.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )

        faixa_inicio = max(inicio, inicio_banco)
        faixa_fim = min(fim, fim_banco)

        segundos_elegiveis = 0

        if faixa_fim > faixa_inicio:
            segundos_elegiveis = int(
                (faixa_fim - faixa_inicio).total_seconds()
            )

        # Tudo fora de 18:01-23:59 é pagamento.
        segundos_fora_banco = total_segundos - segundos_elegiveis
        segundos_pagar += max(0, segundos_fora_banco)

        if segundos_elegiveis <= 0:
            continue

        ja_usado = banco_por_dia.get(dia, 0)
        restante = max(0, limite_banco_dia - ja_usado)

        segundos_para_banco = min(
            segundos_elegiveis,
            restante
        )

        segundos_excedentes = (
            segundos_elegiveis - segundos_para_banco
        )

        segundos_banco += segundos_para_banco
        segundos_pagar += segundos_excedentes

        banco_por_dia[dia] = (
            ja_usado + segundos_para_banco
        )

    return segundos_banco, segundos_pagar


def nome_arquivo_pdf(usuario, competencia_fim):
    nome = usuario["nome"].strip().replace(" ", "_")
    nome = "".join(
        caractere
        for caractere in nome
        if caractere.isalnum() or caractere in ("_", "-")
    )

    return (
        f"Sobreaviso_{nome}_"
        f"{competencia_fim.year}_{competencia_fim.month:02d}.pdf"
    )


def gerar_pdf(
    id_usuario,
    data_referencia=None,
    pasta_saida="pdfs",
):
    """
    Gera um PDF individual do técnico para a competência 11 -> 10.

    Nesta V1 o arquivo apenas extrai os lançamentos já existentes
    em sobreaviso.lancamentos. Ele NÃO gera linhas, NÃO envia e-mail
    e NÃO executa o fechamento do dia 11.
    """

    usuario = buscar_usuario(id_usuario)

    if not usuario:
        raise ValueError(
            f"Usuário {id_usuario} não encontrado ou inativo."
        )

    competencia_inicio, competencia_fim, registros = buscar_lancamentos(
        id_usuario=id_usuario,
        data_referencia=data_referencia,
    )

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)

    caminho_pdf = pasta / nome_arquivo_pdf(
        usuario,
        competencia_fim,
    )

    documento = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="Sobreaviso Mensal T.I.",
        author="Automate - Sobreaviso",
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloSobreaviso",
        parent=estilos["Heading1"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        spaceAfter=5 * mm,
    )

    texto_celula = ParagraphStyle(
        "TextoCelula",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8,
    )

    texto_celula_centro = ParagraphStyle(
        "TextoCelulaCentro",
        parent=texto_celula,
        alignment=TA_CENTER,
    )

    elementos = []

    elementos.append(
        Paragraph(
            "SOBREAVISO MENSAL T.I.",
            titulo,
        )
    )

    cabecalho_info = [
        [
            Paragraph("<b>EMPRESA:</b>", texto_celula),
            Paragraph(usuario["nome_empresa"], texto_celula),
            Paragraph("<b>DEPARTAMENTO:</b>", texto_celula),
            Paragraph(usuario["nome_departamento"], texto_celula),
        ],
        [
            Paragraph("<b>DATA INICIAL:</b>", texto_celula),
            Paragraph(
                competencia_inicio.strftime("%d/%m/%Y"),
                texto_celula,
            ),
            Paragraph("<b>DATA FINAL:</b>", texto_celula),
            Paragraph(
                competencia_fim.strftime("%d/%m/%Y"),
                texto_celula,
            ),
        ],
        [
            Paragraph("<b>FUNCIONÁRIO:</b>", texto_celula),
            Paragraph(usuario["nome"], texto_celula),
            Paragraph("<b>CHAPA:</b>", texto_celula),
            Paragraph(str(usuario["chapa"] or ""), texto_celula),
        ],
    ]

    tabela_info = Table(
        cabecalho_info,
        colWidths=[
            28 * mm,
            72 * mm,
            30 * mm,
            72 * mm,
        ],
        hAlign="LEFT",
    )

    tabela_info.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elementos.append(tabela_info)
    elementos.append(Spacer(1, 4 * mm))

    dados = [
        [
            "CHAPA",
            "NOME",
            "DT SOBREAVISO",
            "HORA INICIAL",
            "HORA FINAL",
            "MÊS",
            "OBSERVAÇÕES",
            "TIPO",
            "HORAS TOTAIS",
            "DIA DA SEMANA",
        ]
    ]

    total_segundos = 0
    total_acionamentos = 0

    for registro in registros:
        inicio = registro["data_hora_inicio"]
        fim = registro["data_hora_fim"]
        tipo = registro["tipo"]

        total_segundos += max(
            0,
            int((fim - inicio).total_seconds()),
        )

        if tipo == "ACIONAMENTO":
            total_acionamentos += 1

        observacao = registro["motivo"] or ""

        dados.append(
            [
                Paragraph(
                    str(usuario["chapa"] or ""),
                    texto_celula_centro,
                ),
                Paragraph(usuario["nome"], texto_celula),
                Paragraph(
                    inicio.strftime("%d/%m/%Y"),
                    texto_celula_centro,
                ),
                Paragraph(
                    inicio.strftime("%H:%M"),
                    texto_celula_centro,
                ),
                Paragraph(
                    fim.strftime("%H:%M"),
                    texto_celula_centro,
                ),
                Paragraph(
                    MESES_PT[inicio.month],
                    texto_celula_centro,
                ),
                Paragraph(
                    observacao,
                    texto_celula,
                ),
                Paragraph(
                    tipo,
                    texto_celula_centro,
                ),
                Paragraph(
                    formatar_duracao(inicio, fim),
                    texto_celula_centro,
                ),
                Paragraph(
                    DIAS_SEMANA_PT[inicio.weekday()],
                    texto_celula_centro,
                ),
            ]
        )

    if len(dados) == 1:
        dados.append(
            [
                "",
                Paragraph(
                    "Nenhum lançamento encontrado para esta competência.",
                    texto_celula,
                ),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    tabela = Table(
        dados,
        repeatRows=1,
        colWidths=[
            14 * mm,   # chapa
            38 * mm,   # nome
            22 * mm,   # data
            20 * mm,   # hora inicial
            20 * mm,   # hora final
            18 * mm,   # mês
            54 * mm,   # observações
            24 * mm,   # tipo
            22 * mm,   # horas
            27 * mm,   # dia semana
        ],
        hAlign="LEFT",
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#D9E1F2"),
                ),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]
        )
    )

    elementos.append(tabela)
    elementos.append(Spacer(1, 5 * mm))

    horas_totais = total_segundos // 3600
    minutos_totais = (total_segundos % 3600) // 60

    if usuario["banco_de_horas"]:

        segundos_banco, segundos_pagar = calcular_banco_horas(
            registros,
            usuario
        )

        resumo = Table(
            [
                [
                    Paragraph(
                        "<b>Quantidade de acionamentos:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        str(total_acionamentos),
                        texto_celula,
                    ),
                    Paragraph(
                        "<b>Total de horas lançadas:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        f"{horas_totais:02d}:{minutos_totais:02d}",
                        texto_celula,
                    ),
                    Paragraph(
                        "<b>Banco de horas:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        formatar_segundos(segundos_banco),
                        texto_celula,
                    ),
                    Paragraph(
                        "<b>Horas a pagar:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        formatar_segundos(segundos_pagar),
                        texto_celula,
                    ),
                ]
            ],
            colWidths=[
                37 * mm,
                14 * mm,
                34 * mm,
                20 * mm,
                28 * mm,
                20 * mm,
                28 * mm,
                20 * mm,
            ],
            hAlign="LEFT",
        )

        resumo.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("BACKGROUND", (0, 0), (0, 0), colors.whitesmoke),
                    ("BACKGROUND", (2, 0), (2, 0), colors.whitesmoke),
                    ("BACKGROUND", (4, 0), (4, 0), colors.whitesmoke),
                    ("BACKGROUND", (6, 0), (6, 0), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

    else:

        resumo = Table(
            [
                [
                    Paragraph(
                        "<b>Quantidade de acionamentos:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        str(total_acionamentos),
                        texto_celula,
                    ),
                    Paragraph(
                        "<b>Total de horas lançadas:</b>",
                        texto_celula,
                    ),
                    Paragraph(
                        f"{horas_totais:02d}:{minutos_totais:02d}",
                        texto_celula,
                    ),
                ]
            ],
            colWidths=[
                40 * mm,
                18 * mm,
                40 * mm,
                25 * mm,
            ],
            hAlign="LEFT",
        )

        resumo.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("BACKGROUND", (0, 0), (0, 0), colors.whitesmoke),
                    ("BACKGROUND", (2, 0), (2, 0), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

    elementos.append(resumo)

    documento.build(elementos)

    return caminho_pdf


def ler_data_referencia(valor):
    valor = valor.strip()

    if not valor:
        return date.today()

    return datetime.strptime(
        valor,
        "%d/%m/%Y",
    ).date()


if __name__ == "__main__":
    print("=== EXTRATOR DE SOBREAVISO ===")

    id_usuario = int(
        input("ID do usuário: ").strip()
    )

    referencia = input(
        "Data de referência [DD/MM/AAAA] "
        "(Enter = hoje): "
    )

    data_referencia = ler_data_referencia(referencia)

    competencia_inicio, competencia_fim = calcular_competencia(
        data_referencia
    )

    print(
        "Competência selecionada: "
        f"{competencia_inicio:%d/%m/%Y} "
        f"até {competencia_fim:%d/%m/%Y}"
    )

    arquivo = gerar_pdf(
        id_usuario=id_usuario,
        data_referencia=data_referencia,
    )

    print(f"PDF gerado: {arquivo}")

# ============================================================
# FUNÇÕES DE APOIO DO FRONT DE EXTRAÇÃO
# ============================================================

MESES_EXTRACAO = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def listar_tecnicos_extracao():
    """
    Compatibilidade com o front_extrator antigo.
    Lista todos os técnicos ativos.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_usuario,
                nome
            FROM sobreaviso.usuarios
            WHERE ativo = TRUE
              AND perfil = 'TECNICO'
            ORDER BY nome;
        """)

        return cur.fetchall()


def listar_competencias_extracao():
    """
    Retorna as competências no formato:
        Julho - Agosto
        Agosto - Setembro

    O valor é o mês final da competência.
    """

    competencias = {}

    for mes_fim in range(1, 13):

        mes_inicio = (
            12
            if mes_fim == 1
            else mes_fim - 1
        )

        nome = (
            f"{MESES_EXTRACAO[mes_inicio - 1]} - "
            f"{MESES_EXTRACAO[mes_fim - 1]}"
        )

        competencias[nome] = mes_fim

    return competencias


def montar_data_referencia_competencia(
    ano,
    mes_fim
):
    """
    Monta uma data de referência dentro do mês final.
    O dia 14 é usado apenas como referência para calcular
    a competência 11 do mês anterior até 10 do mês final.
    """

    return date(
        int(ano),
        int(mes_fim),
        14
    )


def consultar_extracao(
    id_usuario,
    ano,
    mes_fim
):
    """
    Compatibilidade com o front_extrator antigo.
    """

    data_referencia = (
        montar_data_referencia_competencia(
            ano=ano,
            mes_fim=mes_fim
        )
    )

    competencia_inicio, competencia_fim, registros = (
        buscar_lancamentos(
            id_usuario=id_usuario,
            data_referencia=data_referencia
        )
    )

    return {
        "id_usuario": id_usuario,
        "data_referencia": data_referencia,
        "competencia_inicio": competencia_inicio,
        "competencia_fim": competencia_fim,
        "registros": registros
    }


# ============================================================
# PERMISSÕES DA EXTRAÇÃO
# ============================================================

def _buscar_perfil_extracao(
    id_usuario_executor
):
    with conn.cursor() as cur:

        cur.execute("""
            SELECT perfil
            FROM sobreaviso.usuarios
            WHERE id_usuario = %s
              AND ativo = TRUE;
        """, (id_usuario_executor,))

        resultado = cur.fetchone()

    if not resultado:
        raise ValueError(
            "Usuário executor não encontrado ou inativo."
        )

    return str(resultado[0]).upper()


def _ids_subordinados_extracao(
    id_usuario_gestor
):
    with conn.cursor() as cur:

        cur.execute("""
            WITH RECURSIVE subordinados AS
            (
                SELECT
                    u.id_usuario,
                    u.id_gestor
                FROM sobreaviso.usuarios u
                WHERE u.id_gestor = %s
                  AND u.ativo = TRUE

                UNION ALL

                SELECT
                    u.id_usuario,
                    u.id_gestor
                FROM sobreaviso.usuarios u

                INNER JOIN subordinados s
                    ON u.id_gestor = s.id_usuario

                WHERE u.ativo = TRUE
            )

            SELECT DISTINCT
                id_usuario
            FROM subordinados;
        """, (id_usuario_gestor,))

        return {
            linha[0]
            for linha in cur.fetchall()
        }


def validar_permissao_extracao(
    id_usuario_executor,
    id_usuario_alvo
):
    """
    ADMIN:
        pode extrair de qualquer técnico.

    GESTOR:
        pode extrair somente dos técnicos abaixo dele.

    TECNICO:
        pode extrair somente o próprio PDF.
    """

    perfil = _buscar_perfil_extracao(
        id_usuario_executor
    )

    if perfil == "ADMIN":
        return True

    if perfil == "TECNICO":

        if id_usuario_executor != id_usuario_alvo:
            raise PermissionError(
                "Técnico sem permissão para extrair "
                "PDF de outro usuário."
            )

        return True

    if perfil == "GESTOR":

        subordinados = _ids_subordinados_extracao(
            id_usuario_executor
        )

        if id_usuario_alvo not in subordinados:
            raise PermissionError(
                "Gestor sem permissão para extrair "
                "PDF deste usuário."
            )

        return True

    raise PermissionError(
        f"Perfil sem permissão para extração: {perfil}"
    )


def listar_usuarios_permitidos_extracao(
    id_usuario_executor
):
    """
    Lista os usuários que podem aparecer no front de extração.
    """

    perfil = _buscar_perfil_extracao(
        id_usuario_executor
    )

    with conn.cursor() as cur:

        if perfil == "ADMIN":

            cur.execute("""
                SELECT
                    id_usuario,
                    nome
                FROM sobreaviso.usuarios
                WHERE ativo = TRUE
                  AND perfil = 'TECNICO'
                ORDER BY nome;
            """)

            return cur.fetchall()

        if perfil == "GESTOR":

            cur.execute("""
                WITH RECURSIVE subordinados AS
                (
                    SELECT
                        u.id_usuario,
                        u.nome,
                        u.perfil,
                        u.id_gestor
                    FROM sobreaviso.usuarios u
                    WHERE u.id_gestor = %s
                      AND u.ativo = TRUE

                    UNION ALL

                    SELECT
                        u.id_usuario,
                        u.nome,
                        u.perfil,
                        u.id_gestor
                    FROM sobreaviso.usuarios u

                    INNER JOIN subordinados s
                        ON u.id_gestor = s.id_usuario

                    WHERE u.ativo = TRUE
                )

                SELECT DISTINCT
                    id_usuario,
                    nome
                FROM subordinados
                WHERE perfil = 'TECNICO'
                ORDER BY nome;
            """, (id_usuario_executor,))

            return cur.fetchall()

        if perfil == "TECNICO":

            cur.execute("""
                SELECT
                    id_usuario,
                    nome
                FROM sobreaviso.usuarios
                WHERE id_usuario = %s
                  AND ativo = TRUE;
            """, (id_usuario_executor,))

            return cur.fetchall()

    return []


def consultar_extracao_permitida(
    id_usuario_executor,
    id_usuario_alvo,
    ano,
    mes_fim
):
    validar_permissao_extracao(
        id_usuario_executor,
        id_usuario_alvo
    )

    return consultar_extracao(
        id_usuario=id_usuario_alvo,
        ano=ano,
        mes_fim=mes_fim
    )


def gerar_pdf_permitido(
    id_usuario_executor,
    id_usuario_alvo,
    data_referencia=None,
    pasta_saida="pdfs"
):
    validar_permissao_extracao(
        id_usuario_executor,
        id_usuario_alvo
    )

    return gerar_pdf(
        id_usuario=id_usuario_alvo,
        data_referencia=data_referencia,
        pasta_saida=pasta_saida
    )