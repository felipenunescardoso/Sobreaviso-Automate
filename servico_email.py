import smtplib
import ssl
import time as time_module

from datetime import datetime, date, time, timedelta
from email.message import EmailMessage
from pathlib import Path

from inicio import conn
from configurador_email import buscar_configuracao_email
from extrator_pdf import gerar_pdf, calcular_competencia


NOME_SERVICO = "E-mail"
INTERVALO_VERIFICACAO_SEGUNDOS = 7200


# ============================================================
# AUXILIARES DE BANCO
# ============================================================

def _commit():
    conn.commit()


def _rollback():
    conn.rollback()


# ============================================================
# CONFIGURAÇÃO DO SERVIÇO
# ============================================================

def buscar_configuracao_servico():
    """
    Busca a configuração do serviço E-mail.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                nome,
                periodicidade,
                dia,
                hora,
                ativo
            FROM sobreaviso.configuracao_servicos
            WHERE LOWER(nome) = LOWER(%s)
            LIMIT 1;
        """, (NOME_SERVICO,))

        linha = cur.fetchone()

    if not linha:
        return None

    return {
        "id": linha[0],
        "nome": linha[1],
        "periodicidade": linha[2],
        "dia": linha[3],
        "hora": linha[4],
        "ativo": linha[5],
    }


def buscar_ultima_execucao(id_servico):
    """
    Considera a última execução registrada no log.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(data_hora_execucao)
            FROM sobreaviso.logs_servicos
            WHERE id_servico = %s;
        """, (id_servico,))

        linha = cur.fetchone()

    return linha[0] if linha and linha[0] else None


def deve_executar(config, agora=None):
    """
    Regras:
      DIARIO  -> 1 dia
      SEMANAL -> 7 dias
      MENSAL  -> 30 dias
      ANUAL   -> 365 dias

    O campo hora define a hora mínima do dia para a execução.
    O campo dia é mantido como configuração de referência.

    Se nunca executou, roda assim que atingir a hora configurada.
    """

    if agora is None:
        agora = datetime.now()

    if not config["ativo"]:
        return False

    periodicidade = str(config["periodicidade"]).upper().strip()

    intervalos = {
        "DIARIO": timedelta(days=1),
        "SEMANAL": timedelta(days=7),
        "MENSAL": timedelta(days=30),
        "ANUAL": timedelta(days=365),
    }

    if periodicidade not in intervalos:
        raise ValueError(
            f"Periodicidade inválida para o serviço {config['nome']}: "
            f"{config['periodicidade']}"
        )

    hora_configurada = config["hora"]

    if isinstance(hora_configurada, str):
        hora_configurada = time.fromisoformat(hora_configurada)

    horario_minimo_hoje = datetime.combine(
        agora.date(),
        hora_configurada
    )

    if agora < horario_minimo_hoje:
        return False

    ultima_execucao = buscar_ultima_execucao(config["id"])

    if not ultima_execucao:
        return True

    return agora >= ultima_execucao + intervalos[periodicidade]


# ============================================================
# LOG
# ============================================================

def gravar_log(id_servico, nome_servico, status, mensagem):
    """
    Um log por tentativa de envio.
    """

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.logs_servicos
                (
                    id_servico,
                    nome_servico,
                    status,
                    mensagem
                )
                VALUES (%s, %s, %s, %s);
            """, (
                id_servico,
                nome_servico,
                status,
                mensagem
            ))

        _commit()

    except Exception:
        _rollback()
        raise


# ============================================================
# USUÁRIOS COM ESCALA NO PERÍODO
# ============================================================

def buscar_usuarios_periodo(data_referencia=None):
    """
    Retorna todos os usuários que tiveram qualquer interseção
    de escala com a competência 11 -> 10.
    """

    competencia_inicio, competencia_fim = calcular_competencia(
        data_referencia
    )

    inicio = datetime.combine(
        competencia_inicio,
        time(0, 0)
    )

    fim_exclusivo = datetime.combine(
        competencia_fim + timedelta(days=1),
        time(0, 0)
    )

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                u.id_usuario,
                u.nome,
                u.email,
                u.id_empresa
            FROM sobreaviso.escalas e

            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario

            WHERE e.data_hora_inicio < %s
              AND e.data_hora_fim >= %s
              AND u.ativo = TRUE

            ORDER BY u.nome;
        """, (
            fim_exclusivo,
            inicio
        ))

        linhas = cur.fetchall()

    return (
        competencia_inicio,
        competencia_fim,
        [
            {
                "id_usuario": linha[0],
                "nome": linha[1],
                "email": linha[2],
                "id_empresa": linha[3],
            }
            for linha in linhas
        ]
    )


# ============================================================
# DESTINATÁRIOS
# ============================================================

def buscar_destinatarios_sobreaviso(id_usuario):
    """
    Destinatários:
      1. próprio usuário;
      2. gestor direto do departamento;
      3. recebedores extras cadastrados.

    Para os recebedores extras, como a tabela guarda apenas e-mail,
    o próprio e-mail é usado como identificação no log.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                u.nome,
                u.email,
                u.id_departamento,
                r.emails
            FROM sobreaviso.usuarios u

            LEFT JOIN sobreaviso.recebedores r
                ON r.id_usuario = u.id_usuario
               AND r.ativo = TRUE

            WHERE u.id_usuario = %s
              AND u.ativo = TRUE;
        """, (id_usuario,))

        usuario = cur.fetchone()

        if not usuario:
            return []

        nome_usuario = usuario[0]
        email_usuario = usuario[1]
        id_departamento = usuario[2]
        emails_extras = usuario[3]

        cur.execute("""
            SELECT
                ug.nome,
                ug.email
            FROM sobreaviso.gestor_departamento gd

            INNER JOIN sobreaviso.usuarios ug
                ON ug.id_usuario = gd.id_usuario

            WHERE gd.id_departamento = %s
              AND ug.ativo = TRUE

            ORDER BY gd.id_gestor_departamento
            LIMIT 1;
        """, (id_departamento,))

        gestor = cur.fetchone()

    destinatarios = []

    if email_usuario:
        destinatarios.append({
            "nome": nome_usuario,
            "email": email_usuario.strip(),
            "tipo": "USUARIO"
        })

    if gestor and gestor[1]:
        destinatarios.append({
            "nome": gestor[0],
            "email": gestor[1].strip(),
            "tipo": "GESTOR"
        })

    if emails_extras:
        for email in emails_extras.split(";"):
            email = email.strip()

            if email:
                destinatarios.append({
                    "nome": email,
                    "email": email,
                    "tipo": "RECEBEDOR"
                })

    # Remove duplicidades por e-mail
    unicos = {}

    for destinatario in destinatarios:
        chave = destinatario["email"].lower()

        if chave not in unicos:
            unicos[chave] = destinatario

    return list(unicos.values())


def formatar_destinatarios_log(destinatarios):
    partes = []

    for destinatario in destinatarios:
        partes.append(
            f"{destinatario['nome']} <{destinatario['email']}>"
        )

    return "; ".join(partes)


# ============================================================
# ENVIO SMTP
# ============================================================

def enviar_email_sobreaviso(
    configuracao,
    usuario,
    destinatarios,
    caminho_pdf
):
    """
    Envia um único e-mail com o PDF individual do usuário.
    """

    (
        id_configuracao,
        id_empresa,
        protocolo,
        servidor,
        porta,
        usuario_smtp,
        senha_smtp,
        usar_tls,
        usar_ssl,
        email_remetente,
        nome_remetente,
        ativo
    ) = configuracao

    if not ativo:
        raise ValueError(
            "A configuração de e-mail da empresa está inativa."
        )

    if str(protocolo).upper() != "SMTP":
        raise ValueError(
            "O envio automático exige protocolo SMTP."
        )

    if not destinatarios:
        raise ValueError(
            "Nenhum destinatário encontrado para o usuário."
        )

    mensagem = EmailMessage()

    mensagem["Subject"] = (
        f"Envio Automático Sobreaviso ({usuario['nome']})"
    )

    mensagem["From"] = (
        f"{nome_remetente} <{email_remetente}>"
        if nome_remetente
        else email_remetente
    )

    mensagem["To"] = ", ".join(
        d["email"]
        for d in destinatarios
    )

    mensagem.set_content(
        f"Segue em anexo o relatório de sobreaviso de "
        f"{usuario['nome']}."
    )

    caminho_pdf = Path(caminho_pdf)

    with caminho_pdf.open("rb") as arquivo:
        conteudo_pdf = arquivo.read()

    mensagem.add_attachment(
        conteudo_pdf,
        maintype="application",
        subtype="pdf",
        filename=caminho_pdf.name
    )

    contexto_ssl = ssl.create_default_context()

    if usar_ssl:
        with smtplib.SMTP_SSL(
            servidor,
            int(porta),
            context=contexto_ssl,
            timeout=60
        ) as smtp:

            if usuario_smtp:
                smtp.login(
                    usuario_smtp,
                    senha_smtp
                )

            smtp.send_message(mensagem)

    else:
        with smtplib.SMTP(
            servidor,
            int(porta),
            timeout=60
        ) as smtp:

            smtp.ehlo()

            if usar_tls:
                smtp.starttls(
                    context=contexto_ssl
                )
                smtp.ehlo()

            if usuario_smtp:
                smtp.login(
                    usuario_smtp,
                    senha_smtp
                )

            smtp.send_message(mensagem)


# ============================================================
# EXECUÇÃO DO LOTE
# ============================================================

def executar_envios():
    """
    Executa o lote da competência atual.

    Gera um PDF por usuário e grava um log após cada tentativa
    de envio.
    """

    config_servico = buscar_configuracao_servico()

    if not config_servico:
        raise ValueError(
            "Serviço E-mail não cadastrado em configuracao_servicos."
        )

    competencia_inicio, competencia_fim, usuarios = (
        buscar_usuarios_periodo(
            data_referencia=date.today()
        )
    )

    print(
        f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
        f"Competência: "
        f"{competencia_inicio:%d/%m/%Y} até "
        f"{competencia_fim:%d/%m/%Y}"
    )

    print(
        f"Usuários com escala no período: {len(usuarios)}"
    )

    for usuario in usuarios:

        destinatarios = []

        try:
            configuracao_email = buscar_configuracao_email(
                usuario["id_empresa"]
            )

            if not configuracao_email:
                raise ValueError(
                    f"Empresa {usuario['id_empresa']} não possui "
                    f"configuração de e-mail."
                )

            destinatarios = buscar_destinatarios_sobreaviso(
                usuario["id_usuario"]
            )

            if not destinatarios:
                raise ValueError(
                    "Nenhum destinatário válido encontrado."
                )

            caminho_pdf = gerar_pdf(
                id_usuario=usuario["id_usuario"],
                data_referencia=date.today()
            )

            enviar_email_sobreaviso(
                configuracao=configuracao_email,
                usuario=usuario,
                destinatarios=destinatarios,
                caminho_pdf=caminho_pdf
            )

            nomes_destinatarios = formatar_destinatarios_log(
                destinatarios
            )

            mensagem_log = (
                f"Usuário: {usuario['nome']} | "
                f"Competência: "
                f"{competencia_inicio:%d/%m/%Y} a "
                f"{competencia_fim:%d/%m/%Y} | "
                f"Destinatários: {nomes_destinatarios}"
            )

            gravar_log(
                id_servico=config_servico["id"],
                nome_servico=config_servico["nome"],
                status="SUCESSO",
                mensagem=mensagem_log
            )

            print(
                f"SUCESSO | {usuario['nome']} | "
                f"{nomes_destinatarios}"
            )

        except Exception as erro:

            nomes_destinatarios = (
                formatar_destinatarios_log(destinatarios)
                if destinatarios
                else "Não identificados"
            )

            mensagem_log = (
                f"Usuário: {usuario['nome']} | "
                f"Destinatários: {nomes_destinatarios} | "
                f"Erro: {erro}"
            )

            try:
                gravar_log(
                    id_servico=config_servico["id"],
                    nome_servico=config_servico["nome"],
                    status="ERRO",
                    mensagem=mensagem_log
                )
            except Exception as erro_log:
                print(
                    f"ERRO AO GRAVAR LOG | "
                    f"{usuario['nome']} | {erro_log}"
                )

            print(
                f"ERRO | {usuario['nome']} | {erro}"
            )


# ============================================================
# LOOP DO SERVIÇO
# ============================================================

def iniciar_servico():
    """
    Processo contínuo para instalação como serviço no servidor.
    """

    print("=" * 70)
    print("SERVIÇO DE ENVIO AUTOMÁTICO DE SOBREAVISO")
    print("=" * 70)

    while True:

        try:
            configuracao = buscar_configuracao_servico()

            if not configuracao:
                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Configuração do serviço não encontrada."
                )

            elif not configuracao["ativo"]:
                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Serviço inativo."
                )

            elif deve_executar(configuracao):
                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Iniciando lote de envio."
                )

                executar_envios()

                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Lote finalizado."
                )

        except Exception as erro:
            print(
                f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                f"Erro no loop do serviço: {erro}"
            )

        time_module.sleep(
            INTERVALO_VERIFICACAO_SEGUNDOS
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    iniciar_servico()