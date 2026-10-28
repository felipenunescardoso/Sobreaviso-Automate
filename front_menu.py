import streamlit as st
import runpy

from inicio import conn
from pathlib import Path
from datetime import datetime


# ============================================================
# AUTENTICAÇÃO
# ============================================================

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

if not st.session_state["usuario"]:
    caminho_login = Path(__file__).resolve().parent / "front_main.py"

    if not caminho_login.exists():
        st.error("Arquivo front_main.py não encontrado.")
        st.stop()

    runpy.run_path(
        str(caminho_login),
        run_name="__main__"
    )

    st.stop()


# ============================================================
# CONFIGURAÇÃO DA PÁGINA APÓS LOGIN
# ============================================================

st.set_page_config(
    page_title="Sobreaviso Automate",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

usuario = st.session_state["usuario"]

nome_usuario = usuario.get("nome", "Usuário")
id_usuario_logado = usuario.get("id_usuario")
perfil = str(usuario.get("perfil", "")).upper()
nome_departamento = usuario.get("nome_departamento", "")

if "pagina" not in st.session_state or not st.session_state["pagina"]:
    st.session_state["pagina"] = "inicio"


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
            rgba(79, 110, 247, 0.05),
            transparent 25%
        ),
        #F7F9FC;
    color: #111827;
}

.block-container {
    padding-top: 2rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1600px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #111827 0%,
        #172033 100%
    );
}

[data-testid="stSidebar"] * {
    color: #F9FAFB;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 42px;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    color: #E5E7EB !important;
    text-align: left;
    justify-content: flex-start;
    font-weight: 600;
}

[data-testid="stSidebar"] .stButton > button:hover {
    border: 1px solid #345BEB;
    background: rgba(52, 91, 235, 0.15);
    color: white !important;
}

[data-testid="stSidebar"] .stButton > button * {
    color: inherit !important;
}

/* Alinhamento dos nomes das telas */
[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    justify-content: flex-start !important;
}

[data-testid="stSidebar"] .stButton > button > div,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {
    width: 100%;
    text-align: left !important;
    justify-content: flex-start !important;
}

.logo-box {
    padding: 8px 4px 20px 4px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 16px;
}

.logo-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: white;
}

.logo-subtitle {
    margin-top: 4px;
    font-size: 16px;
    color: #AAB4C5;
}

.sidebar-section {
    margin-top: 18px;
    margin-bottom: 7px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #8D99AA;
    text-align: left;
}

.sidebar-user {
    margin-top: 24px;
    padding: 14px;
    border-radius: 12px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.07);
}

.sidebar-user-name {
    font-weight: 700;
    font-size: 14px;
}

.sidebar-user-info {
    font-size: 12px;
    margin-top: 4px;
    color: #AAB4C5;
}

.page-title {
    font-size: 35px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.7px;
    color: #111827;
    margin-bottom: 4px;
}

.page-subtitle {
    font-size: 15px;
    color: #697386;
    margin-bottom: 24px;
}

.info-card {
    background: white;
    border: 1px solid #E2E7EF;
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    min-height: 112px;
}

.info-card-title {
    font-size: 13px;
    color: #697386;
    font-weight: 600;
    margin-bottom: 8px;
}

.info-card-value {
    font-size: 24px;
    color: #111827;
    font-weight: 800;
}

.info-card-small {
    margin-top: 5px;
    font-size: 12px;
    color: #98A2B3;
}

.quick-card {
    background: white;
    border: 1px solid #E2E7EF;
    border-radius: 16px;
    padding: 22px;
    height: 210px;
    box-sizing: border-box;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.quick-icon {
    font-size: 28px;
    margin-bottom: 10px;
}

.quick-title {
    font-size: 17px;
    font-weight: 800;
    color: #111827;
}

.quick-text {
    margin-top: 5px;
    font-size: 13px;
    line-height: 1.4;
    color: #697386;
}

.section-title {
    margin-top: 28px;
    margin-bottom: 14px;
    font-size: 21px;
    font-weight: 800;
    color: #111827;
}

div.stButton > button {
    border-radius: 10px !important;
    min-height: 42px !important;
    font-weight: 700 !important;
    border: 1px solid #151A24 !important;
    background: linear-gradient(180deg, #171C27 0%, #10141D 100%) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div.stButton > button p,
div.stButton > button span,
div.stButton > button div {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div.stButton > button:hover {
    border-color: #635BFF !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(16, 24, 40, 0.18) !important;
}

/* Tabela de plantonistas */
div[data-testid="stDataFrame"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 12px !important;
    overflow: hidden !important;
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
# PLANTONISTAS ATUAIS
# ============================================================

def buscar_plantonistas_atuais():

    with conn.cursor() as cur:

        cur.execute("""
            SELECT DISTINCT
                u.nome,
                d.nome_departamento AS departamento
            FROM sobreaviso.escalas e
            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario
            LEFT JOIN sobreaviso.departamentos d
                ON d.id_departamento = u.id_departamento
            WHERE e.data_hora_inicio::date <= CURRENT_DATE
              AND e.data_hora_fim >= CURRENT_TIMESTAMP
              AND u.ativo = TRUE
            ORDER BY
                d.nome_departamento,
                u.nome;
        """)

        return cur.fetchall()


# ============================================================
# PRÓXIMAS ESCALAS DO USUÁRIO LOGADO
# ============================================================

def buscar_proximas_escalas_usuario(id_usuario):

    if not id_usuario:
        return []

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                e.data_hora_inicio,
                e.data_hora_fim,
                e.ordem
            FROM sobreaviso.escalas e
            WHERE e.id_usuario = %s
              AND e.data_hora_inicio > CURRENT_TIMESTAMP
            ORDER BY e.data_hora_inicio
            LIMIT 2;
        """, (id_usuario,))

        return cur.fetchall()


# ============================================================
# NAVEGAÇÃO
# ============================================================

def navegar(pagina):
    """
    Guarda a página desejada na sessão.

    O app.py poderá usar esta chave para fazer o roteamento
    definitivo das telas.
    """
    st.session_state["pagina"] = pagina
    st.rerun()


def botao_menu(label, pagina, key):
    if st.button(
        label,
        key=key,
        use_container_width=True
    ):
        navegar(pagina)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="logo-box">
            <div class="logo-title">⏱ SOBREAVISO AUTOMATE</div>
            <div class="logo-subtitle">Gestão de escalas e acionamentos</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    botao_menu(
        "🏠  Início",
        "inicio",
        "menu_inicio"
    )

    # ========================================================
    # ADMIN
    # ========================================================

    if perfil == "ADMIN":

        st.markdown(
            '<div class="sidebar-section">GESTÃO</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "👤  Usuários",
            "usuarios",
            "menu_usuarios"
        )

        botao_menu(
            "🏢  Departamentos",
            "departamentos",
            "menu_departamentos"
        )

        st.markdown(
            '<div class="sidebar-section">OPERAÇÃO</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "⚡  Acionamentos",
            "acionamentos",
            "menu_acionamentos"
        )

        botao_menu(
            "📅  Cadastro de Escalas",
            "escalas",
            "menu_escalas"
        )

        botao_menu(
            "📄  Extrair PDFs",
            "extrair_pdfs",
            "menu_extrair"
        )

        st.markdown(
            '<div class="sidebar-section">CONFIGURAÇÃO</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "✉️  Configuração de E-mail",
            "configurador_email",
            "menu_config_email"
        )

    # ========================================================
    # GESTOR
    # ========================================================

    elif perfil == "GESTOR":

        st.markdown(
            '<div class="sidebar-section">GESTÃO DO DEPARTAMENTO</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "👤  Usuários",
            "usuarios",
            "menu_usuarios"
        )

        botao_menu(
            "⚡  Acionamentos",
            "acionamentos",
            "menu_acionamentos"
        )

        botao_menu(
            "📅  Cadastro de Escalas",
            "escalas",
            "menu_escalas"
        )

        botao_menu(
            "📄  Extrair PDFs",
            "extrair_pdfs",
            "menu_extrair"
        )

    # ========================================================
    # TÉCNICO
    # ========================================================

    elif perfil == "TECNICO":

        st.markdown(
            '<div class="sidebar-section">GESTÃO</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "👤  Usuários",
            "usuarios",
            "menu_usuarios"
        )

        st.markdown(
            '<div class="sidebar-section">MINHAS OPERAÇÕES</div>',
            unsafe_allow_html=True
        )

        botao_menu(
            "⚡  Acionamentos",
            "acionamentos",
            "menu_acionamentos"
        )

        botao_menu(
            "📅  Minhas Escalas",
            "escalas",
            "menu_escalas"
        )

        botao_menu(
            "📄  Extrair meus PDFs",
            "extrair_pdfs",
            "menu_extrair"
        )

    else:
        st.warning(
            f"Perfil não reconhecido: {perfil}"
        )

    # ========================================================
    # USUÁRIO / LOGOUT
    # ========================================================

    st.markdown(
        f"""
        <div class="sidebar-user">
            <div class="sidebar-user-name">
                👤 {nome_usuario}
            </div>
            <div class="sidebar-user-info">
                {perfil.title()}
                {" • " + nome_departamento if nome_departamento else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "↪  Sair",
        key="menu_sair",
        use_container_width=True
    ):
        st.session_state["pagina"] = "inicio"
        st.session_state["usuario"] = None
        st.rerun()


# ============================================================
# ROTEAMENTO DAS TELAS
# ============================================================

ARQUIVOS_PAGINAS = {
    "usuarios": "front_usuarios.py",
    "departamentos": "front_departamentos.py",
    "acionamentos": "front_preenchimento.py",
    "escalas": "front_escalas.py",
    "extrair_pdfs": "front_extrator.py",
    "configurador_email": "front_config_email.py",
}

PAGINAS_PERMITIDAS = {
    "ADMIN": {
        "inicio",
        "usuarios",
        "departamentos",
        "acionamentos",
        "escalas",
        "extrair_pdfs",
        "configurador_email",
    },
    "GESTOR": {
        "inicio",
        "usuarios",
        "acionamentos",
        "escalas",
        "extrair_pdfs",
    },
    "TECNICO": {
        "inicio",
        "usuarios",
        "acionamentos",
        "escalas",
        "extrair_pdfs",
    },
}

def executar_front(nome_arquivo):
    caminho = Path(__file__).resolve().parent / nome_arquivo

    if not caminho.exists():
        st.error(f"Arquivo não encontrado: {nome_arquivo}")
        st.stop()

    set_page_config_original = st.set_page_config

    try:
        st.set_page_config = lambda *args, **kwargs: None

        runpy.run_path(
            str(caminho),
            run_name="__main__"
        )

    finally:
        st.set_page_config = set_page_config_original


pagina_atual = st.session_state.get("pagina", "inicio")

if pagina_atual not in PAGINAS_PERMITIDAS.get(perfil, {"inicio"}):
    st.error("Seu perfil não possui permissão para acessar esta tela.")
    st.session_state["pagina"] = "inicio"
    st.stop()

if pagina_atual != "inicio":
    arquivo = ARQUIVOS_PAGINAS.get(pagina_atual)

    if not arquivo:
        st.error("Tela não configurada no menu.")
        st.stop()

    executar_front(arquivo)
    st.stop()


# ============================================================
# CONTEÚDO INICIAL DO MENU
# ============================================================

agora = datetime.now()

primeiro_nome = (
    nome_usuario.split()[0]
    if nome_usuario
    else "Usuário"
)

st.markdown(
    f'<div class="page-title">Olá, {primeiro_nome}!</div>',
    unsafe_allow_html=True
)

if perfil == "ADMIN":
    subtitulo = (
        "Visão geral administrativa do Sobreaviso Automate."
    )

elif perfil == "GESTOR":
    subtitulo = (
        "Gerencie os acionamentos e as escalas do seu departamento."
    )

else:
    subtitulo = (
        "Consulte seus acionamentos e relatórios de sobreaviso."
    )

st.markdown(
    f'<div class="page-subtitle">{subtitulo}</div>',
    unsafe_allow_html=True
)


# ============================================================
# DATA / PERFIL
# ============================================================

col_data, col_hora, col_perfil = st.columns(3)

with col_data:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">Hoje</div>
            <div class="info-card-value">
                {agora:%d/%m/%Y}
            </div>
            <div class="info-card-small">
                Data atual
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_hora:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">Horário</div>
            <div class="info-card-value">
                {agora:%H:%M}
            </div>
            <div class="info-card-small">
                Horário do sistema
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_perfil:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">Perfil</div>
            <div class="info-card-value">
                {perfil.title()}
            </div>
            <div class="info-card-small">
                {nome_departamento or "Sem departamento"}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ACESSO RÁPIDO
# ============================================================

st.markdown(
    '<div class="section-title">Acesso rápido</div>',
    unsafe_allow_html=True
)


# ============================================================
# ADMIN - CARDS
# ============================================================

if perfil == "ADMIN":

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">👤</div>
                <div class="quick-title">Usuários</div>
                <div class="quick-text">
                    Cadastre técnicos, gestores e administradores.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Usuários",
            key="card_admin_usuarios",
            use_container_width=True
        ):
            navegar("usuarios")

    with col2:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📅</div>
                <div class="quick-title">Escalas</div>
                <div class="quick-text">
                    Cadastre e administre as escalas de sobreaviso.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Escalas",
            key="card_admin_escalas",
            use_container_width=True
        ):
            navegar("escalas")

    with col3:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">⚡</div>
                <div class="quick-title">Acionamentos</div>
                <div class="quick-text">
                    Consulte e administre os acionamentos registrados.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Acionamentos",
            key="card_admin_acionamentos",
            use_container_width=True
        ):
            navegar("acionamentos")

    with col4:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📄</div>
                <div class="quick-title">Extrair PDFs</div>
                <div class="quick-text">
                    Gere os relatórios individuais de sobreaviso.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Extrair PDFs",
            key="card_admin_pdf",
            use_container_width=True
        ):
            navegar("extrair_pdfs")


# ============================================================
# GESTOR - CARDS
# ============================================================

elif perfil == "GESTOR":

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">👤</div>
                <div class="quick-title">Minha Equipe</div>
                <div class="quick-text">
                    Consulte e edite seu cadastro e os usuários sob sua gestão.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Usuários",
            key="card_gestor_usuarios",
            use_container_width=True
        ):
            navegar("usuarios")

    with col2:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">⚡</div>
                <div class="quick-title">Acionamentos</div>
                <div class="quick-text">
                    Consulte e ajuste acionamentos do seu departamento.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Acionamentos",
            key="card_gestor_acionamentos",
            use_container_width=True
        ):
            navegar("acionamentos")

    with col3:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📅</div>
                <div class="quick-title">Cadastro de Escalas</div>
                <div class="quick-text">
                    Configure as escalas dos técnicos sob sua gestão.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Escalas",
            key="card_gestor_escalas",
            use_container_width=True
        ):
            navegar("escalas")

    with col4:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📄</div>
                <div class="quick-title">Extrair PDFs</div>
                <div class="quick-text">
                    Gere relatórios dos usuários do seu departamento.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Extrair PDFs",
            key="card_gestor_pdf",
            use_container_width=True
        ):
            navegar("extrair_pdfs")


# ============================================================
# TÉCNICO - CARDS
# ============================================================

elif perfil == "TECNICO":

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">👤</div>
                <div class="quick-title">Meu Cadastro</div>
                <div class="quick-text">
                    Atualize seus dados pessoais e sua senha.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Meu Cadastro",
            key="card_tecnico_usuarios",
            use_container_width=True
        ):
            navegar("usuarios")

    with col2:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">⚡</div>
                <div class="quick-title">Meus Acionamentos</div>
                <div class="quick-text">
                    Registre e consulte seus acionamentos de sobreaviso.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Acionamentos",
            key="card_tecnico_acionamentos",
            use_container_width=True
        ):
            navegar("acionamentos")

    with col3:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📄</div>
                <div class="quick-title">Meus PDFs</div>
                <div class="quick-text">
                    Gere seus relatórios individuais de sobreaviso.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Extrair PDFs",
            key="card_tecnico_pdf",
            use_container_width=True
        ):
            navegar("extrair_pdfs")


    with col4:
        st.markdown(
            """
            <div class="quick-card">
                <div class="quick-icon">📅</div>
                <div class="quick-title">Minhas Escalas</div>
                <div class="quick-text">
                    Consulte e edite suas escalas de sobreaviso.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Abrir Minhas Escalas",
            key="card_tecnico_escalas",
            use_container_width=True
        ):
            navegar("escalas")


# ============================================================
# PLANTONISTAS ATUAIS + MINHAS PRÓXIMAS ESCALAS
# ============================================================

col_plantonistas, col_minhas_escalas = st.columns(2)

with col_plantonistas:
    st.markdown(
        '<div class="section-title">Plantonistas atuais</div>',
        unsafe_allow_html=True
    )

    erro_plantonistas = None

    try:
        plantonistas = buscar_plantonistas_atuais()
    except Exception as erro:
        plantonistas = []
        erro_plantonistas = erro
        st.error(f"Erro ao consultar plantonistas atuais: {erro}")

    if plantonistas:
        dados_plantonistas = [
            {
                "Nome": nome,
                "Departamento": departamento or "-"
            }
            for nome, departamento in plantonistas
        ]

        st.dataframe(
            dados_plantonistas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nome": st.column_config.TextColumn("Nome", width="medium"),
                "Departamento": st.column_config.TextColumn(
                    "Departamento",
                    width="medium"
                )
            }
        )

    elif erro_plantonistas is None:
        st.info("Nenhum plantonista no momento.")


try:
    proximas_escalas = buscar_proximas_escalas_usuario(
        id_usuario_logado
    )
    erro_proximas_escalas = None
except Exception as erro:
    proximas_escalas = []
    erro_proximas_escalas = erro


# A coluna da direita só recebe conteúdo quando houver
# escala futura do próprio usuário (ou erro real de consulta).
if proximas_escalas:
    with col_minhas_escalas:
        st.markdown(
            '<div class="section-title">Minhas próximas escalas</div>',
            unsafe_allow_html=True
        )

        dados_escalas = []

        for data_inicio, data_fim, ordem in proximas_escalas:
            dados_escalas.append(
                {
                    "Início": data_inicio.strftime("%d/%m/%Y %H:%M"),
                    "Fim": data_fim.strftime("%d/%m/%Y %H:%M"),
                    "Ordem": ordem
                }
            )

        st.dataframe(
            dados_escalas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Início": st.column_config.TextColumn(
                    "Início",
                    width="medium"
                ),
                "Fim": st.column_config.TextColumn(
                    "Fim",
                    width="medium"
                ),
                "Ordem": st.column_config.NumberColumn(
                    "Ordem",
                    format="%d"
                )
            }
        )

elif erro_proximas_escalas is not None:
    with col_minhas_escalas:
        st.error(
            f"Erro ao consultar suas próximas escalas: "
            f"{erro_proximas_escalas}"
        )


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#98A2B3;
        font-size:12px;
        margin-top:48px;
    ">
        Sobreaviso Automate • Versão 1.0.0
    </div>
    """,
    unsafe_allow_html=True
)