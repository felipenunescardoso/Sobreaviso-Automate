import streamlit as st

from cadastros import listar_empresas
from configurador_email import (
    buscar_configuracao_email,
    salvar_configuracao_email,
    testar_smtp
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Configuração de E-mail",
    page_icon="✉️",
    layout="wide"
)


# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}

.stApp {
    background: #F7F9FC;
    color: #111827;
}

.block-container {
    padding-top: 2.2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}

.titulo-pagina {
    font-size: 38px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 8px;
}

.subtitulo-pagina {
    font-size: 16px;
    color: #697386;
    margin-bottom: 28px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border-radius: 16px;
}

div.stButton > button {
    border-radius: 10px;
    min-height: 44px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    '<div class="titulo-pagina">Configuração de E-mail</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-pagina">'
    'Configure o servidor SMTP utilizado pelo envio automático de sobreavisos.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# EMPRESAS
# ============================================================

try:
    empresas = listar_empresas(apenas_ativas=True)

except Exception as erro:
    st.error(
        f"Erro ao carregar empresas: {erro}"
    )
    empresas = []


if not empresas:

    st.warning(
        "Nenhuma empresa ativa cadastrada."
    )

    st.stop()


mapa_empresas = {
    empresa[0]: empresa[1]
    for empresa in empresas
}


id_empresa = st.selectbox(
    "Empresa",
    options=list(mapa_empresas.keys()),
    format_func=lambda x: mapa_empresas[x]
)


# ============================================================
# BUSCAR CONFIGURAÇÃO ATUAL
# ============================================================

try:

    configuracao = buscar_configuracao_email(
        id_empresa
    )

except Exception as erro:

    st.error(
        f"Erro ao carregar configuração: {erro}"
    )

    configuracao = None


# ============================================================
# VALORES PADRÃO / EXISTENTES
# ============================================================

if configuracao:

    (
        id_configuracao,
        id_empresa_config,
        protocolo_atual,
        servidor_atual,
        porta_atual,
        usuario_atual,
        senha_atual,
        usar_tls_atual,
        usar_ssl_atual,
        email_remetente_atual,
        nome_remetente_atual,
        ativo_atual
    ) = configuracao

else:

    protocolo_atual = "SMTP"
    servidor_atual = ""
    porta_atual = 587
    usuario_atual = ""
    senha_atual = ""
    usar_tls_atual = True
    usar_ssl_atual = False
    email_remetente_atual = ""
    nome_remetente_atual = "Sobreaviso Automate"
    ativo_atual = True


# ============================================================
# CONFIGURAÇÃO SMTP
# ============================================================

st.markdown("### Servidor de e-mail")

with st.container(
    border=True,
    key="config_email_card"
):

    col1, col2 = st.columns(2)

    with col1:

        protocolo = st.selectbox(
            "Protocolo",
            options=[
                "SMTP"
            ],
            index=0
        )

    with col2:

        ativo = st.checkbox(
            "Configuração ativa",
            value=ativo_atual
        )


    col3, col4 = st.columns(
        [3, 1]
    )

    with col3:

        servidor = st.text_input(
            "Servidor SMTP",
            value=servidor_atual,
            placeholder="smtp.office365.com"
        )

    with col4:

        porta = st.number_input(
            "Porta",
            min_value=1,
            max_value=65535,
            value=int(porta_atual),
            step=1
        )


    col5, col6 = st.columns(2)

    with col5:

        usuario = st.text_input(
            "Usuário",
            value=usuario_atual or "",
            placeholder="sobreaviso@empresa.com"
        )

    with col6:

        senha = st.text_input(
            "Senha",
            value=senha_atual or "",
            type="password"
        )


    col7, col8 = st.columns(2)

    with col7:

        usar_tls = st.checkbox(
            "Usar TLS",
            value=usar_tls_atual
        )

    with col8:

        usar_ssl = st.checkbox(
            "Usar SSL",
            value=usar_ssl_atual
        )


    st.markdown("### Remetente")


    col9, col10 = st.columns(2)

    with col9:

        email_remetente = st.text_input(
            "E-mail remetente",
            value=email_remetente_atual or "",
            placeholder="sobreaviso@empresa.com"
        )

    with col10:

        nome_remetente = st.text_input(
            "Nome do remetente",
            value=nome_remetente_atual or "",
            placeholder="Sobreaviso Automate"
        )


    # ========================================================
    # SALVAR
    # ========================================================

    salvar = st.button(
        "Salvar configuração",
        type="primary",
        use_container_width=True
    )


    if salvar:

        if not servidor.strip():

            st.error(
                "Informe o servidor SMTP."
            )

        elif not email_remetente.strip():

            st.error(
                "Informe o e-mail remetente."
            )

        elif usar_tls and usar_ssl:

            st.error(
                "Selecione TLS ou SSL, não os dois ao mesmo tempo."
            )

        else:

            try:

                id_configuracao = salvar_configuracao_email(
                    id_empresa=id_empresa,
                    protocolo=protocolo,
                    servidor=servidor.strip(),
                    porta=int(porta),
                    usuario=usuario.strip()
                    if usuario
                    else None,
                    senha=senha
                    if senha
                    else None,
                    usar_tls=usar_tls,
                    usar_ssl=usar_ssl,
                    email_remetente=email_remetente.strip(),
                    nome_remetente=nome_remetente.strip()
                    if nome_remetente
                    else None,
                    ativo=ativo
                )

                st.success(
                    f"Configuração salva com sucesso. "
                    f"ID: {id_configuracao}"
                )

            except Exception as erro:

                st.error(
                    f"Erro ao salvar configuração: {erro}"
                )


# ============================================================
# TESTE DE ENVIO
# ============================================================

st.markdown("---")
st.markdown("### Teste de envio")

with st.container(
    border=True,
    key="teste_email_card"
):

    st.write(
        "Envie uma mensagem de teste utilizando "
        "a configuração SMTP salva para esta empresa."
    )

    email_teste = st.text_input(
        "E-mail para teste",
        placeholder="usuario@empresa.com"
    )

    testar = st.button(
        "Enviar e-mail de teste",
        use_container_width=True
    )


    if testar:

        if not email_teste.strip():

            st.error(
                "Informe um e-mail para o teste."
            )

        else:

            try:

                testar_smtp(
                    id_empresa=id_empresa,
                    email_destino=email_teste.strip()
                )

                st.success(
                    "E-mail de teste enviado com sucesso."
                )

            except Exception as erro:

                st.error(
                    f"Falha no teste de envio: {erro}"
                )


# ============================================================
# INFORMAÇÕES
# ============================================================

st.markdown("---")

st.info(
    "Esta tela configura somente o servidor de envio. "
    "A rotina automática que busca os usuários com escala, gera os PDFs "
    "e envia para o próprio usuário, gestor e recebedores será tratada "
    "separadamente."
)