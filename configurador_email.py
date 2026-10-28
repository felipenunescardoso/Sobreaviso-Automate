import smtplib
import ssl

from email.message import EmailMessage

from inicio import conn


# ============================================================
# AUXILIARES
# ============================================================

def _commit():
    conn.commit()


def _rollback():
    conn.rollback()


# ============================================================
# CONFIGURAÇÃO
# ============================================================

def buscar_configuracao_email(id_empresa):

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                id_configuracao,
                id_empresa,
                protocolo,
                servidor,
                porta,
                usuario,
                senha,
                usar_tls,
                usar_ssl,
                email_remetente,
                nome_remetente,
                ativo
            FROM sobreaviso.configuracao_email
            WHERE id_empresa = %s;
        """, (id_empresa,))

        return cur.fetchone()


def salvar_configuracao_email(
    id_empresa,
    protocolo,
    servidor,
    porta,
    usuario,
    senha,
    usar_tls,
    usar_ssl,
    email_remetente,
    nome_remetente=None,
    ativo=True
):

    try:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO sobreaviso.configuracao_email
                (
                    id_empresa,
                    protocolo,
                    servidor,
                    porta,
                    usuario,
                    senha,
                    usar_tls,
                    usar_ssl,
                    email_remetente,
                    nome_remetente,
                    ativo
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )

                ON CONFLICT (id_empresa)

                DO UPDATE
                   SET protocolo = EXCLUDED.protocolo,
                       servidor = EXCLUDED.servidor,
                       porta = EXCLUDED.porta,
                       usuario = EXCLUDED.usuario,
                       senha = EXCLUDED.senha,
                       usar_tls = EXCLUDED.usar_tls,
                       usar_ssl = EXCLUDED.usar_ssl,
                       email_remetente = EXCLUDED.email_remetente,
                       nome_remetente = EXCLUDED.nome_remetente,
                       ativo = EXCLUDED.ativo

                RETURNING id_configuracao;
            """, (
                id_empresa,
                protocolo,
                servidor,
                porta,
                usuario,
                senha,
                usar_tls,
                usar_ssl,
                email_remetente,
                nome_remetente,
                ativo
            ))

            id_configuracao = cur.fetchone()[0]

        _commit()

        return id_configuracao

    except Exception:
        _rollback()
        raise


# ============================================================
# TESTE SMTP
# ============================================================

def testar_smtp(id_empresa, email_destino):

    config = buscar_configuracao_email(id_empresa)

    if not config:
        raise ValueError(
            "Configuração de e-mail não encontrada."
        )

    (
        id_configuracao,
        id_empresa,
        protocolo,
        servidor,
        porta,
        usuario,
        senha,
        usar_tls,
        usar_ssl,
        email_remetente,
        nome_remetente,
        ativo
    ) = config

    if not ativo:
        raise ValueError(
            "Configuração de e-mail está inativa."
        )

    if protocolo != "SMTP":
        raise ValueError(
            "O teste de envio exige configuração SMTP."
        )

    mensagem = EmailMessage()

    mensagem["Subject"] = "Teste de envio - Sobreaviso Automate"

    mensagem["From"] = (
        f"{nome_remetente} <{email_remetente}>"
        if nome_remetente
        else email_remetente
    )

    mensagem["To"] = email_destino

    mensagem.set_content(
        "Este é um teste de envio do Sobreaviso Automate."
    )

    contexto_ssl = ssl.create_default_context()

    if usar_ssl:

        with smtplib.SMTP_SSL(
            servidor,
            porta,
            context=contexto_ssl
        ) as smtp:

            if usuario:
                smtp.login(
                    usuario,
                    senha
                )

            smtp.send_message(
                mensagem
            )

    else:

        with smtplib.SMTP(
            servidor,
            porta
        ) as smtp:

            smtp.ehlo()

            if usar_tls:
                smtp.starttls(
                    context=contexto_ssl
                )

                smtp.ehlo()

            if usuario:
                smtp.login(
                    usuario,
                    senha
                )

            smtp.send_message(
                mensagem
            )

    return True