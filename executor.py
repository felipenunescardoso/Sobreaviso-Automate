from datetime import date, datetime, time, timedelta

from inicio import conn


TIPO_SOBREAVISO = "SOBREAVISO"
TIPO_ACIONAMENTO = "ACIONAMENTO"
ORIGEM_AUTOMATICO = "AUTOMATICO"
ORIGEM_USUARIO = "USUARIO"

FIM_MANHA = time(8, 0)
INICIO_NOITE = time(18, 0)


def _commit():
    conn.commit()


def _rollback():
    conn.rollback()


def calcular_minutos(inicio, fim):
    if fim <= inicio:
        return 0
    return int((fim - inicio).total_seconds() // 60)


def formatar_minutos(minutos):
    h, m = divmod(int(minutos), 60)
    return f"{h}h{m:02d}m"


# ============================================================
# COMPETÊNCIA 11 -> 10
# ============================================================

def _inicio_competencia(data_referencia):
    if data_referencia.day >= 11:
        return date(data_referencia.year, data_referencia.month, 11)

    primeiro_dia_mes = date(data_referencia.year, data_referencia.month, 1)
    mes_anterior = primeiro_dia_mes - timedelta(days=1)
    return date(mes_anterior.year, mes_anterior.month, 11)


def _proximo_inicio_competencia(competencia_inicio):
    if competencia_inicio.month == 12:
        return date(competencia_inicio.year + 1, 1, 11)
    return date(competencia_inicio.year, competencia_inicio.month + 1, 11)


def _fim_competencia(competencia_inicio):
    return _proximo_inicio_competencia(competencia_inicio) - timedelta(days=1)


# ============================================================
# ESCALA / USUÁRIO
# ============================================================

def buscar_escala(id_usuario, id_escala):
    """A escala só é válida se pertencer ao usuário informado."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                e.id_escala,
                e.id_usuario,
                e.data_hora_inicio,
                e.data_hora_fim,
                e.ordem,
                e.replicacao,
                e.encerrada,
                e.data_hora_encerramento,
                u.id_cidade,
                u.uf
            FROM sobreaviso.escalas e
            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario
            WHERE e.id_escala = %s
              AND e.id_usuario = %s;
        """, (id_escala, id_usuario))
        return cur.fetchone()


def buscar_escala_permitida(
    id_usuario_executor,
    id_usuario,
    id_escala
):
    """
    Consulta destinada ao front.
    Valida a hierarquia antes de retornar a escala.
    """

    validar_permissao_usuario(
        id_usuario_executor,
        id_usuario
    )

    return buscar_escala(
        id_usuario,
        id_escala
    )


def _validar_escala(id_usuario, id_escala):
    escala = buscar_escala(id_usuario, id_escala)
    if not escala:
        raise ValueError("Escala não encontrada para o usuário informado.")
    return escala


def buscar_perfil_usuario(id_usuario):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT perfil
            FROM sobreaviso.usuarios
            WHERE id_usuario = %s
              AND ativo = TRUE;
        """, (id_usuario,))
        resultado = cur.fetchone()

    if not resultado:
        raise ValueError("Usuário executor não encontrado ou inativo.")

    return resultado[0]


def listar_ids_subordinados(id_usuario_gestor):
    """
    Retorna todos os subordinados ativos abaixo do gestor,
    incluindo níveis indiretos da hierarquia usuarios.id_gestor.
    """

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


def validar_permissao_usuario(
    id_usuario_executor,
    id_usuario_alvo
):
    """
    Regra de acesso aos acionamentos:

    ADMIN:
        pode operar qualquer usuário.

    GESTOR:
        pode operar ele mesmo e usuários abaixo dele na hierarquia.

    TECNICO:
        pode operar somente ele mesmo.
    """

    perfil = str(
        buscar_perfil_usuario(
            id_usuario_executor
        )
    ).upper()

    if perfil == "ADMIN":
        return True

    if perfil == "TECNICO":

        if id_usuario_executor != id_usuario_alvo:
            raise PermissionError(
                "Técnico sem permissão para operar "
                "acionamentos de outro usuário."
            )

        return True

    if perfil == "GESTOR":

        if id_usuario_executor == id_usuario_alvo:
            return True

        subordinados = listar_ids_subordinados(
            id_usuario_executor
        )

        if id_usuario_alvo not in subordinados:
            raise PermissionError(
                "Gestor sem permissão para operar "
                "acionamentos deste usuário."
            )

        return True

    raise PermissionError(
        f"Perfil sem permissão para operar acionamentos: {perfil}"
    )


def listar_usuarios_permitidos_acionamentos(
    id_usuario_executor
):
    """
    Lista os usuários que podem aparecer no front de acionamentos.

    ADMIN:
        todos os técnicos ativos.

    GESTOR:
        ele mesmo e técnicos ativos abaixo dele na hierarquia.

    TECNICO:
        apenas ele mesmo.
    """

    perfil = str(
        buscar_perfil_usuario(
            id_usuario_executor
        )
    ).upper()

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
                ),

                permitidos AS
                (
                    SELECT
                        u.id_usuario,
                        u.nome
                    FROM sobreaviso.usuarios u
                    WHERE u.id_usuario = %s
                      AND u.ativo = TRUE

                    UNION

                    SELECT
                        s.id_usuario,
                        s.nome
                    FROM subordinados s
                    WHERE s.perfil = 'TECNICO'
                )

                SELECT DISTINCT
                    id_usuario,
                    nome
                FROM permitidos
                ORDER BY nome;
            """, (
                id_usuario_executor,
                id_usuario_executor
            ))

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

    raise PermissionError(
        f"Perfil sem permissão para listar usuários: {perfil}"
    )


def validar_permissao_periodo(id_usuario_executor, data_hora_lancamento):
    """
    ADMIN/GESTOR podem alterar períodos fechados.

    TECNICO: a partir do dia 12, não pode criar/alterar/excluir
    lançamentos do dia 10 ou anterior do mesmo mês/ano.

    Operações de SISTEMA não usam esta validação.
    """
    perfil = buscar_perfil_usuario(id_usuario_executor)

    if perfil in ("ADMIN", "GESTOR"):
        return True

    hoje = date.today()

    if (
        perfil == "TECNICO"
        and hoje.day >= 12
        and data_hora_lancamento.year == hoje.year
        and data_hora_lancamento.month == hoje.month
        and data_hora_lancamento.day <= 10
    ):
        raise ValueError(
            "O período até o dia 10 desta competência está fechado. "
            "Procure seu gestor."
        )

    return True


def buscar_escala_sistema(id_escala):
    """
    Operação interna: não valida usuário executor/dono.
    Descobre o dono da escala pelo id_escala.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                e.id_escala,
                e.id_usuario,
                e.data_hora_inicio,
                e.data_hora_fim,
                e.ordem,
                e.replicacao,
                e.encerrada,
                e.data_hora_encerramento,
                u.id_cidade,
                u.uf
            FROM sobreaviso.escalas e
            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario
            WHERE e.id_escala = %s;
        """, (id_escala,))
        return cur.fetchone()


# ============================================================
# FERIADOS / FAIXAS BASE
# ============================================================

def eh_feriado(data_referencia, uf=None, id_cidade=None):
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


def _dia_integral(data_referencia, uf, id_cidade):
    if data_referencia.weekday() >= 5:
        return True
    return eh_feriado(data_referencia, uf, id_cidade)


def _faixas_base_dia(data_referencia, uf, id_cidade):
    """Intervalos [inicio, fim): limites exatos, sem ajuste de 1 minuto."""
    inicio_dia = datetime.combine(data_referencia, time(0, 0))
    proximo_dia = inicio_dia + timedelta(days=1)

    if _dia_integral(data_referencia, uf, id_cidade):
        return [(inicio_dia, proximo_dia)]

    return [
        (inicio_dia, datetime.combine(data_referencia, FIM_MANHA)),
        (datetime.combine(data_referencia, INICIO_NOITE), proximo_dia),
    ]


def _intersecao(inicio_a, fim_a, inicio_b, fim_b):
    inicio = max(inicio_a, inicio_b)
    fim = min(fim_a, fim_b)
    if fim <= inicio:
        return None
    return inicio, fim


# ============================================================
# COMPETÊNCIAS DA ESCALA
# ============================================================

def gerar_competencias_escala(id_usuario, id_escala):
    escala = _validar_escala(id_usuario, id_escala)
    escala_inicio = escala[2]
    escala_fim = escala[3]

    competencia_inicio = _inicio_competencia(escala_inicio.date())
    ids = []

    try:
        with conn.cursor() as cur:
            while True:
                competencia_fim = _fim_competencia(competencia_inicio)
                proximo_inicio = _proximo_inicio_competencia(competencia_inicio)
                limite_proxima = datetime.combine(proximo_inicio, time(0, 0))

                trecho_inicio = max(
                    escala_inicio,
                    datetime.combine(competencia_inicio, time(0, 0))
                )
                trecho_fim = min(escala_fim, limite_proxima)

                if trecho_fim > trecho_inicio:
                    cur.execute("""
                        INSERT INTO sobreaviso.escala_competencias
                        (
                            id_escala,
                            competencia_inicio,
                            competencia_fim,
                            data_hora_inicio,
                            data_hora_fim
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT
                        (
                            id_escala,
                            competencia_inicio,
                            competencia_fim
                        )
                        DO UPDATE
                           SET data_hora_inicio = EXCLUDED.data_hora_inicio,
                               data_hora_fim = EXCLUDED.data_hora_fim
                        RETURNING id_escala_competencia;
                    """, (
                        id_escala,
                        competencia_inicio,
                        competencia_fim,
                        trecho_inicio,
                        trecho_fim
                    ))
                    ids.append(cur.fetchone()[0])

                if escala_fim <= limite_proxima:
                    break

                competencia_inicio = proximo_inicio

        _commit()
        return ids

    except Exception:
        _rollback()
        raise


def _buscar_competencia_por_data(id_usuario, id_escala, data_hora):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                ec.id_escala_competencia,
                ec.data_hora_inicio,
                ec.data_hora_fim,
                ec.bloqueada,
                ec.processada
            FROM sobreaviso.escala_competencias ec
            INNER JOIN sobreaviso.escalas e
                ON e.id_escala = ec.id_escala
            WHERE ec.id_escala = %s
              AND e.id_usuario = %s
              AND %s >= ec.data_hora_inicio
              AND %s <= ec.data_hora_fim
            ORDER BY ec.data_hora_inicio
            LIMIT 1;
        """, (id_escala, id_usuario, data_hora, data_hora))
        return cur.fetchone()


# ============================================================
# ACIONAMENTOS
# ============================================================

def _listar_acionamentos(id_usuario, id_escala):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                l.id_lancamento,
                l.id_escala_competencia,
                l.data_hora_inicio,
                l.data_hora_fim,
                l.motivo,
                l.quantidade_minutos
            FROM sobreaviso.lancamentos l
            INNER JOIN sobreaviso.escala_competencias ec
                ON ec.id_escala_competencia = l.id_escala_competencia
            INNER JOIN sobreaviso.escalas e
                ON e.id_escala = ec.id_escala
            WHERE e.id_escala = %s
              AND e.id_usuario = %s
              AND l.tipo = 'ACIONAMENTO'
            ORDER BY l.data_hora_inicio, l.id_lancamento;
        """, (id_escala, id_usuario))
        return cur.fetchall()


def _buscar_acionamento(id_usuario, id_lancamento):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                l.id_lancamento,
                l.id_escala_competencia,
                ec.id_escala,
                l.data_hora_inicio,
                l.data_hora_fim,
                l.motivo
            FROM sobreaviso.lancamentos l
            INNER JOIN sobreaviso.escala_competencias ec
                ON ec.id_escala_competencia = l.id_escala_competencia
            INNER JOIN sobreaviso.escalas e
                ON e.id_escala = ec.id_escala
            WHERE l.id_lancamento = %s
              AND l.tipo = 'ACIONAMENTO'
              AND e.id_usuario = %s;
        """, (id_lancamento, id_usuario))
        return cur.fetchone()


def _validar_acionamento_na_faixa(escala, inicio, fim):
    escala_inicio = escala[2]
    escala_fim = escala[3]
    id_cidade = escala[8]
    uf = escala[9]

    if fim <= inicio:
        raise ValueError("O fim do acionamento deve ser maior que o início.")

    if inicio < escala_inicio or fim > escala_fim:
        raise ValueError("O acionamento está fora do período da escala.")

    if inicio.date() != fim.date():
        raise ValueError("Na V1, um acionamento não pode atravessar a meia-noite.")

    valido = any(
        inicio >= faixa_inicio and fim <= faixa_fim
        for faixa_inicio, faixa_fim in _faixas_base_dia(
            inicio.date(), uf, id_cidade
        )
    )

    if not valido:
        raise ValueError(
            "O acionamento está em horário comercial ou fora de uma faixa válida de sobreaviso."
        )


def _validar_sobreposicao(cur, id_usuario, id_escala, inicio, fim, ignorar_id=None):
    sql = """
        SELECT EXISTS
        (
            SELECT 1
            FROM sobreaviso.lancamentos l
            INNER JOIN sobreaviso.escala_competencias ec
                ON ec.id_escala_competencia = l.id_escala_competencia
            INNER JOIN sobreaviso.escalas e
                ON e.id_escala = ec.id_escala
            WHERE e.id_escala = %s
              AND e.id_usuario = %s
              AND l.tipo = 'ACIONAMENTO'
              AND l.data_hora_inicio < %s
              AND l.data_hora_fim > %s
    """
    params = [id_escala, id_usuario, fim, inicio]

    if ignorar_id is not None:
        sql += " AND l.id_lancamento <> %s "
        params.append(ignorar_id)

    sql += ");"
    cur.execute(sql, tuple(params))

    if bool(cur.fetchone()[0]):
        raise ValueError("Já existe outro acionamento neste intervalo.")


# ============================================================
# MOTOR DE SOBREAVISO
# ============================================================

def _subtrair_acionamentos(faixa_inicio, faixa_fim, acionamentos):
    """Subtrai acionamentos de intervalos [inicio, fim), sem lacunas."""
    segmentos = [(faixa_inicio, faixa_fim)]

    for acionamento in acionamentos:
        ac_inicio = acionamento[2]
        ac_fim = acionamento[3]
        novos = []

        for seg_inicio, seg_fim in segmentos:
            if ac_fim <= seg_inicio or ac_inicio >= seg_fim:
                novos.append((seg_inicio, seg_fim))
                continue

            fim_antes = min(ac_inicio, seg_fim)
            if fim_antes > seg_inicio:
                novos.append((seg_inicio, fim_antes))

            inicio_depois = max(ac_fim, seg_inicio)
            if seg_fim > inicio_depois:
                novos.append((inicio_depois, seg_fim))

        segmentos = novos

    return segmentos


def _inserir_sobreaviso(cur, id_escala_competencia, inicio, fim):
    minutos = calcular_minutos(inicio, fim)
    if minutos <= 0:
        return None

    cur.execute("""
        INSERT INTO sobreaviso.lancamentos
        (
            id_escala_competencia,
            tipo,
            data_hora_inicio,
            data_hora_fim,
            quantidade_minutos,
            motivo,
            origem
        )
        VALUES
        (
            %s,
            'SOBREAVISO',
            %s,
            %s,
            %s,
            NULL,
            'AUTOMATICO'
        )
        RETURNING id_lancamento;
    """, (id_escala_competencia, inicio, fim, minutos))

    return cur.fetchone()[0]


def gerar_sobreaviso(id_usuario, id_escala, ate_data_hora):
    """
    Coração do sistema.

    Apaga e recria somente SOBREAVISO automático.
    ACIONAMENTOS nunca são apagados.
    """
    escala = _validar_escala(id_usuario, id_escala)
    escala_inicio = escala[2]
    escala_fim_previsto = escala[3]
    id_cidade = escala[8]
    uf = escala[9]

    if ate_data_hora < escala_inicio:
        raise ValueError("A geração não pode terminar antes do início da escala.")

    limite = min(ate_data_hora, escala_fim_previsto)

    gerar_competencias_escala(id_usuario, id_escala)
    acionamentos = _listar_acionamentos(id_usuario, id_escala)
    acionamentos_ate_limite = [a for a in acionamentos if a[2] <= limite]

    ids_criados = []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.lancamentos l
                USING sobreaviso.escala_competencias ec
                WHERE l.id_escala_competencia = ec.id_escala_competencia
                  AND ec.id_escala = %s
                  AND l.tipo = 'SOBREAVISO'
                  AND l.origem = 'AUTOMATICO';
            """, (id_escala,))

            cur.execute("""
                SELECT
                    id_escala_competencia,
                    data_hora_inicio,
                    data_hora_fim,
                    bloqueada
                FROM sobreaviso.escala_competencias
                WHERE id_escala = %s
                  AND data_hora_inicio <= %s
                ORDER BY data_hora_inicio;
            """, (id_escala, limite))

            competencias = cur.fetchall()

            for id_comp, comp_inicio, comp_fim, bloqueada in competencias:
                if bloqueada:
                    continue

                trecho_inicio = max(escala_inicio, comp_inicio)
                trecho_fim = min(limite, comp_fim, escala_fim_previsto)

                if trecho_fim <= trecho_inicio:
                    continue

                data_atual = trecho_inicio.date()
                data_final = trecho_fim.date()

                while data_atual <= data_final:
                    for faixa_inicio, faixa_fim in _faixas_base_dia(
                        data_atual, uf, id_cidade
                    ):
                        recorte = _intersecao(
                            faixa_inicio,
                            faixa_fim,
                            trecho_inicio,
                            trecho_fim
                        )

                        if not recorte:
                            continue

                        inicio_recortado, fim_recortado = recorte

                        acionamentos_faixa = [
                            a for a in acionamentos_ate_limite
                            if (
                                a[1] == id_comp
                                and a[2] <= fim_recortado
                                and a[3] >= inicio_recortado
                            )
                        ]

                        for seg_inicio, seg_fim in _subtrair_acionamentos(
                            inicio_recortado,
                            fim_recortado,
                            acionamentos_faixa
                        ):
                            novo_id = _inserir_sobreaviso(
                                cur,
                                id_comp,
                                seg_inicio,
                                seg_fim
                            )
                            if novo_id:
                                ids_criados.append(novo_id)

                    data_atual += timedelta(days=1)

        _commit()
        return ids_criados

    except Exception:
        _rollback()
        raise


def _recalcular_apos_acionamento(id_usuario, id_escala):
    escala = _validar_escala(id_usuario, id_escala)
    encerrada = escala[6]
    encerramento = escala[7]
    fim_previsto = escala[3]

    if encerrada:
        return gerar_sobreaviso(
            id_usuario,
            id_escala,
            encerramento if encerramento else fim_previsto
        )

    acionamentos = _listar_acionamentos(id_usuario, id_escala)

    if not acionamentos:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM sobreaviso.lancamentos l
                    USING sobreaviso.escala_competencias ec
                    WHERE l.id_escala_competencia = ec.id_escala_competencia
                      AND ec.id_escala = %s
                      AND l.tipo = 'SOBREAVISO'
                      AND l.origem = 'AUTOMATICO';
                """, (id_escala,))
            _commit()
            return []
        except Exception:
            _rollback()
            raise

    ultimo_acionamento = acionamentos[-1]
    return gerar_sobreaviso(
        id_usuario,
        id_escala,
        ultimo_acionamento[2]
    )


# ============================================================
# CRUD DO USUÁRIO - ACIONAMENTO
# ============================================================

def registrar_acionamento(
    id_usuario,
    id_usuario_executor,
    id_escala,
    data_hora_inicio,
    data_hora_fim,
    motivo
):
    if not motivo or not motivo.strip():
        raise ValueError("Informe o motivo do acionamento.")

    validar_permissao_usuario(
        id_usuario_executor,
        id_usuario
    )

    validar_permissao_periodo(
        id_usuario_executor,
        data_hora_inicio
    )

    escala = _validar_escala(id_usuario, id_escala)

    if escala[6]:
        raise ValueError("A escala já está encerrada.")

    _validar_acionamento_na_faixa(escala, data_hora_inicio, data_hora_fim)
    gerar_competencias_escala(id_usuario, id_escala)

    competencia = _buscar_competencia_por_data(
        id_usuario,
        id_escala,
        data_hora_inicio
    )
    competencia_fim = _buscar_competencia_por_data(
        id_usuario,
        id_escala,
        data_hora_fim
    )

    if not competencia or not competencia_fim or competencia[0] != competencia_fim[0]:
        raise ValueError("Na V1, o acionamento deve permanecer em uma única competência.")

    if competencia[3]:
        raise ValueError("A competência está bloqueada.")

    minutos = calcular_minutos(data_hora_inicio, data_hora_fim)

    try:
        with conn.cursor() as cur:
            _validar_sobreposicao(
                cur,
                id_usuario,
                id_escala,
                data_hora_inicio,
                data_hora_fim
            )

            cur.execute("""
                INSERT INTO sobreaviso.lancamentos
                (
                    id_escala_competencia,
                    tipo,
                    data_hora_inicio,
                    data_hora_fim,
                    quantidade_minutos,
                    motivo,
                    origem
                )
                VALUES
                (
                    %s,
                    'ACIONAMENTO',
                    %s,
                    %s,
                    %s,
                    %s,
                    'USUARIO'
                )
                RETURNING id_lancamento;
            """, (
                competencia[0],
                data_hora_inicio,
                data_hora_fim,
                minutos,
                motivo.strip()
            ))

            id_lancamento = cur.fetchone()[0]

        _commit()

    except Exception:
        _rollback()
        raise

    _recalcular_apos_acionamento(id_usuario, id_escala)
    return id_lancamento


def alterar_acionamento(
    id_usuario,
    id_usuario_executor,
    id_lancamento,
    data_hora_inicio,
    data_hora_fim,
    motivo
):
    validar_permissao_usuario(
        id_usuario_executor,
        id_usuario
    )

    acionamento = _buscar_acionamento(id_usuario, id_lancamento)
    if not acionamento:
        raise ValueError("Acionamento não encontrado para o usuário informado.")

    validar_permissao_periodo(id_usuario_executor, acionamento[3])
    validar_permissao_periodo(id_usuario_executor, data_hora_inicio)

    id_escala = acionamento[2]
    escala = _validar_escala(id_usuario, id_escala)

    if escala[6]:
        raise ValueError("A escala já está encerrada.")

    if not motivo or not motivo.strip():
        raise ValueError("Informe o motivo do acionamento.")

    _validar_acionamento_na_faixa(escala, data_hora_inicio, data_hora_fim)
    gerar_competencias_escala(id_usuario, id_escala)

    competencia = _buscar_competencia_por_data(id_usuario, id_escala, data_hora_inicio)
    competencia_fim = _buscar_competencia_por_data(id_usuario, id_escala, data_hora_fim)

    if not competencia or not competencia_fim or competencia[0] != competencia_fim[0]:
        raise ValueError("O novo intervalo não pertence a uma única competência.")

    minutos = calcular_minutos(data_hora_inicio, data_hora_fim)

    try:
        with conn.cursor() as cur:
            _validar_sobreposicao(
                cur,
                id_usuario,
                id_escala,
                data_hora_inicio,
                data_hora_fim,
                ignorar_id=id_lancamento
            )

            cur.execute("""
                UPDATE sobreaviso.lancamentos
                   SET id_escala_competencia = %s,
                       data_hora_inicio = %s,
                       data_hora_fim = %s,
                       quantidade_minutos = %s,
                       motivo = %s
                 WHERE id_lancamento = %s
                   AND tipo = 'ACIONAMENTO';
            """, (
                competencia[0],
                data_hora_inicio,
                data_hora_fim,
                minutos,
                motivo.strip(),
                id_lancamento
            ))
            alterados = cur.rowcount

        _commit()

    except Exception:
        _rollback()
        raise

    _recalcular_apos_acionamento(id_usuario, id_escala)
    return alterados > 0


def excluir_acionamento(id_usuario, id_usuario_executor, id_lancamento):

    validar_permissao_usuario(
        id_usuario_executor,
        id_usuario
    )

    acionamento = _buscar_acionamento(id_usuario, id_lancamento)
    if not acionamento:
        raise ValueError("Acionamento não encontrado para o usuário informado.")

    validar_permissao_periodo(id_usuario_executor, acionamento[3])

    id_escala = acionamento[2]
    escala = _validar_escala(id_usuario, id_escala)

    if escala[6]:
        raise ValueError("A escala já está encerrada.")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.lancamentos
                WHERE id_lancamento = %s
                  AND tipo = 'ACIONAMENTO';
            """, (id_lancamento,))
            excluidos = cur.rowcount
        _commit()
    except Exception:
        _rollback()
        raise

    _recalcular_apos_acionamento(id_usuario, id_escala)
    return excluidos > 0


# ============================================================
# ENCERRAMENTO - MANUAL / ADMIN / FUTURO AUTO_EXECUTOR
# ============================================================

def encerrar_escala(id_usuario, id_escala, data_hora_encerramento=None):
    """
    Encerra a escala respeitando o menor horário entre
    o momento do encerramento e o fim previsto.

    Regra:
    - se encerrar antes do fim previsto, encerra naquele momento;
    - se encerrar exatamente no fim previsto, usa o fim previsto;
    - se encerrar depois do fim previsto, limita ao fim previsto;
    - sem acionamentos, completa o sobreaviso até o fim efetivo;
    - com acionamentos, preserva os acionamentos e completa o restante.
    """
    escala = _validar_escala(id_usuario, id_escala)

    inicio_escala = escala[2]
    fim_previsto = escala[3]

    informado = (
        data_hora_encerramento
        if data_hora_encerramento is not None
        else datetime.now()
    )

    if informado < inicio_escala:
        raise ValueError(
            "A escala não pode ser encerrada antes do seu início."
        )

    fim_efetivo = min(
        informado,
        fim_previsto
    )

    gerar_sobreaviso(
        id_usuario,
        id_escala,
        fim_efetivo
    )

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.escalas
                   SET encerrada = TRUE,
                       data_hora_encerramento = %s
                 WHERE id_escala = %s
                   AND id_usuario = %s;
            """, (fim_efetivo, id_escala, id_usuario))
            alterados = cur.rowcount
        _commit()
    except Exception:
        _rollback()
        raise

    return {
        "id_usuario": id_usuario,
        "id_escala": id_escala,
        "fim_previsto": fim_previsto,
        "fim_efetivo": fim_efetivo,
        "encerrada": alterados > 0
    }


def encerrar_escala_sistema(id_escala, data_hora_encerramento=None):
    """
    Operação de SISTEMA.

    Usada pelo botão "Fechar escala" e pelo executor automático.
    Não recebe nem valida o usuário que clicou.

    Regra:
    - antes do fim previsto: encerra no momento informado;
    - no fim previsto: encerra no fim previsto;
    - depois do fim previsto: limita ao fim previsto.
    """
    escala = buscar_escala_sistema(id_escala)

    if not escala:
        raise ValueError("Escala não encontrada.")

    id_usuario = escala[1]
    inicio_escala = escala[2]
    fim_previsto = escala[3]
    encerrada = escala[6]

    if encerrada:
        raise ValueError("A escala já está encerrada.")

    informado = (
        data_hora_encerramento
        if data_hora_encerramento is not None
        else datetime.now()
    )

    if informado < inicio_escala:
        raise ValueError(
            "A escala não pode ser encerrada antes do seu início."
        )

    fim_efetivo = min(
        informado,
        fim_previsto
    )

    gerar_sobreaviso(
        id_usuario,
        id_escala,
        fim_efetivo
    )

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.escalas
                   SET encerrada = TRUE,
                       data_hora_encerramento = %s
                 WHERE id_escala = %s;
            """, (fim_efetivo, id_escala))
            alterados = cur.rowcount
        _commit()
    except Exception:
        _rollback()
        raise

    return {
        "id_usuario": id_usuario,
        "id_escala": id_escala,
        "fim_previsto": fim_previsto,
        "fim_efetivo": fim_efetivo,
        "encerrada": alterados > 0,
        "origem": "SISTEMA"
    }


# ============================================================
# CONSULTA / TESTE
# ============================================================

def listar_lancamentos_escala(id_usuario, id_escala):
    _validar_escala(id_usuario, id_escala)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                l.id_lancamento,
                l.tipo,
                l.data_hora_inicio,
                l.data_hora_fim,
                l.quantidade_minutos,
                l.motivo,
                l.origem,
                ec.id_escala_competencia
            FROM sobreaviso.lancamentos l
            INNER JOIN sobreaviso.escala_competencias ec
                ON ec.id_escala_competencia = l.id_escala_competencia
            INNER JOIN sobreaviso.escalas e
                ON e.id_escala = ec.id_escala
            WHERE e.id_escala = %s
              AND e.id_usuario = %s
            ORDER BY l.data_hora_inicio, l.data_hora_fim, l.id_lancamento;
        """, (id_escala, id_usuario))
        return cur.fetchall()


def listar_lancamentos_escala_permitidos(
    id_usuario_executor,
    id_usuario,
    id_escala
):
    """
    Consulta destinada ao front.
    Valida ADMIN/GESTOR/TECNICO antes da listagem.
    """

    validar_permissao_usuario(
        id_usuario_executor,
        id_usuario
    )

    return listar_lancamentos_escala(
        id_usuario,
        id_escala
    )


def imprimir_lancamentos_escala(id_usuario, id_escala):
    linhas = listar_lancamentos_escala(id_usuario, id_escala)

    print()
    print("=" * 110)
    print(f"USUÁRIO {id_usuario} | ESCALA {id_escala}")
    print("=" * 110)

    for linha in linhas:
        (
            id_lancamento,
            tipo,
            inicio,
            fim,
            minutos,
            motivo,
            origem,
            id_competencia
        ) = linha

        print(
            f"{id_lancamento:>4} | "
            f"{tipo:<12} | "
            f"{inicio:%d/%m/%Y %H:%M} -> {fim:%d/%m/%Y %H:%M} | "
            f"{formatar_minutos(minutos):>8} | "
            f"{origem:<10} | COMP {id_competencia} | {motivo or ''}"
        )


# ============================================================
# EXEMPLOS DO TESTE DE MESA
# ============================================================
#
# TESTE 3 - primeiro acionamento:
#
# registrar_acionamento(
#     id_usuario=7,
#     id_usuario_executor=7,
#     id_escala=15,
#     data_hora_inicio=datetime(2026, 8, 20, 22, 0),
#     data_hora_fim=datetime(2026, 8, 20, 22, 30),
#     motivo="Incidente"
# )
#
# Gera automaticamente, até ali:
#   QUA 18:00 -> QUI 00:00 SOBREAVISO
#   QUI 00:00 -> 08:00 SOBREAVISO
#   QUI 18:00 -> 22:00 SOBREAVISO
#   QUI 22:00 -> 22:30 ACIONAMENTO
#
# TESTE 4 / 5 - fechamento manual ou automático:
#
# encerrar_escala(
#     id_usuario=7,
#     id_escala=15,
#     data_hora_encerramento=datetime(2026, 8, 21, 8, 0)
# )
#
# Completa:
#   QUI 22:30 -> SEX 00:00 SOBREAVISO
#   SEX 00:00 -> 08:00 SOBREAVISO
#
# TESTE 6 - encerramento antecipado:
#
# encerrar_escala(
#     id_usuario=7,
#     id_escala=15,
#     data_hora_encerramento=datetime(2026, 8, 20, 23, 0)
# )
#
# Finaliza em:
#   QUI 22:30 -> 23:00 SOBREAVISO


# registrar_acionamento(
#     id_usuario=2,
#     id_usuario_executor=2,
#     id_escala=1,
#     data_hora_inicio=datetime(2026, 8, 15, 22, 0),
#     data_hora_fim=datetime(2026, 8, 15, 22, 30),
#     motivo="Incidente"
# )


# with conn.cursor() as cur:
#     cur.execute("SELECT * FROM sobreaviso.acionamentos;")

#     acionamentos = cur.fetchall()

#     for acionamento in acionamentos:
#         print(acionamento)