import streamlit as st

from inicio import conn
from autenticacao import autenticar_usuario
from cadastros import alterar_senha


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Sobreaviso Automate",
    page_icon="⏱️",
    layout="centered",
    initial_sidebar_state="collapsed"
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
    background:
        radial-gradient(
            circle at top left,
            rgba(99, 91, 255, 0.08),
            transparent 28%
        ),
        #F7F9FC;
    color: #111827;
}

.block-container {
    max-width: 520px;
    padding-top: 7rem;
    padding-bottom: 4rem;
}

.login-titulo {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 6px;
}

.login-subtitulo {
    text-align: center;
    font-size: 15px;
    color: #697386;
    margin-bottom: 28px;
}

div.stButton > button,
div.stFormSubmitButton > button {
    width: 100%;
    border-radius: 10px;
    min-height: 46px;
    font-weight: 700;
    font-size: 14px;
    border: 1px solid #151A24;
    background: linear-gradient(
        180deg,
        #171C27 0%,
        #10141D 100%
    );
    color: white !important;
}

div.stButton > button *,
div.stFormSubmitButton > button * {
    color: white !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    border-color: #635BFF;
    color: white !important;
}

div[data-baseweb="input"] > div {
    border-radius: 10px !important;
    background: #FFFFFF !important;
}

label {
    color: #344054 !important;
    font-weight: 600 !important;
}

[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #E2E7EF;
    border-radius: 18px;
    padding: 28px 30px;
    box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08);
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CONTROLE DE SESSÃO
# ============================================================

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None


# ============================================================
# FUNÇÃO - VALIDAR LOGIN + CHAPA
# ============================================================

def buscar_usuario_por_login_chapa(login, chapa):

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                id_usuario,
                nome
            FROM sobreaviso.usuarios
            WHERE LOWER(login) = LOWER(%s)
              AND chapa = %s
              AND ativo = TRUE
            LIMIT 1;
        """, (
            login.strip(),
            chapa.strip()
        ))

        return cur.fetchone()


# ============================================================
# FUNÇÃO - PLANTONISTAS ATUAIS
# ============================================================

def buscar_plantonistas_atuais():

    with conn.cursor() as cur:

        cur.execute("""
            SELECT DISTINCT
                u.nome,
                d.nome AS departamento
            FROM sobreaviso.escalas e
            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario
            LEFT JOIN sobreaviso.departamentos d
                ON d.id_departamento = u.id_departamento
            WHERE e.data_hora_inicio <= CURRENT_TIMESTAMP
              AND e.data_hora_fim >= CURRENT_TIMESTAMP
              AND u.ativo = TRUE
            ORDER BY
                d.nome,
                u.nome;
        """)

        return cur.fetchall()


# ============================================================
# SE JÁ ESTIVER LOGADO
# ============================================================

if st.session_state["usuario"]:

    usuario_logado = st.session_state["usuario"]

    st.markdown(
        f'<div class="login-titulo">'
        f'Olá, {usuario_logado["nome"]}!'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitulo">'
        'Consulte seus acionamentos e relatórios de sobreaviso.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("### Plantonistas atuais")

    try:

        plantonistas = buscar_plantonistas_atuais()

    except Exception as erro:

        plantonistas = []

        st.error(
            f"Erro ao consultar plantonistas: {erro}"
        )

    if plantonistas:

        dados_plantonistas = []

        for nome, departamento in plantonistas:

            dados_plantonistas.append(
                {
                    "Nome": nome,
                    "Departamento": departamento or "-"
                }
            )

        st.dataframe(
            dados_plantonistas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nome": st.column_config.TextColumn(
                    "Nome",
                    width="medium"
                ),
                "Departamento": st.column_config.TextColumn(
                    "Departamento",
                    width="medium"
                )
            }
        )

    else:

        st.info(
            "Nenhum plantonista no momento."
        )

    st.stop()


# ============================================================
# TELA DE AUTENTICAÇÃO
# ============================================================

st.markdown(
    '<div class="login-titulo">Sobreaviso Automate</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="login-subtitulo">'
    'Entre com seu usuário e senha para acessar o sistema.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOGIN
# ============================================================

with st.form("form_login"):

    login = st.text_input(
        "Usuário",
        placeholder="Digite seu login"
    )

    senha = st.text_input(
        "Senha",
        type="password",
        placeholder="Digite sua senha"
    )

    entrar = st.form_submit_button(
        "Entrar",
        use_container_width=True
    )


# ============================================================
# AUTENTICAÇÃO
# ============================================================

if entrar:

    if not login.strip():

        st.error(
            "Informe o usuário."
        )

    elif not senha:

        st.error(
            "Informe a senha."
        )

    else:

        try:

            usuario = autenticar_usuario(
                login=login.strip(),
                senha=senha
            )

            if not usuario:

                st.error(
                    "Usuário ou senha inválidos."
                )

            else:

                st.session_state["usuario"] = usuario

                st.success(
                    "Autenticação realizada com sucesso."
                )

                st.rerun()

        except Exception as erro:

            st.error(
                f"Erro ao autenticar: {erro}"
            )


# ============================================================
# ALTERAR SENHA
# ============================================================

st.markdown("---")

with st.expander(
    "Alterar senha",
    expanded=False
):

    st.caption(
        "Informe seu usuário e sua chapa "
        "para validar a alteração."
    )

    with st.form(
        "form_alterar_senha"
    ):

        login_troca = st.text_input(
            "Usuário",
            key="alterar_senha_login",
            placeholder="Digite seu login"
        )

        chapa_troca = st.text_input(
            "Chapa",
            key="alterar_senha_chapa",
            placeholder="Digite sua chapa"
        )

        nova_senha = st.text_input(
            "Nova senha",
            type="password",
            key="alterar_senha_nova"
        )

        confirmar_senha = st.text_input(
            "Confirmar nova senha",
            type="password",
            key="alterar_senha_confirmar"
        )

        confirmar_alteracao = (
            st.form_submit_button(
                "Alterar senha",
                use_container_width=True
            )
        )

    if confirmar_alteracao:

        if not login_troca.strip():

            st.error(
                "Informe o usuário."
            )

        elif not chapa_troca.strip():

            st.error(
                "Informe a chapa."
            )

        elif not nova_senha:

            st.error(
                "Informe a nova senha."
            )

        elif nova_senha != confirmar_senha:

            st.error(
                "As senhas não conferem."
            )

        else:

            try:

                usuario_troca = (
                    buscar_usuario_por_login_chapa(
                        login=login_troca,
                        chapa=chapa_troca
                    )
                )

                if not usuario_troca:

                    st.error(
                        "Usuário ou chapa inválidos."
                    )

                else:

                    id_usuario = usuario_troca[0]

                    alterado = alterar_senha(
                        id_usuario=id_usuario,
                        nova_senha=nova_senha
                    )

                    if alterado:

                        st.success(
                            "Senha alterada com sucesso."
                        )

                    else:

                        st.error(
                            "Não foi possível alterar a senha."
                        )

            except Exception as erro:

                st.error(
                    f"Erro ao alterar senha: {erro}"
                )
