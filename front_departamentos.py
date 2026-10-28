import streamlit as st

from cadastros import (
    listar_empresas,
    listar_departamentos,
    listar_gestores,
    cadastrar_departamento,
    alterar_departamento,
    excluir_departamento
)


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

st.set_page_config(
    page_title="Departamentos",
    page_icon="🏢",
    layout="wide"
)


st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(88, 101, 242, 0.05), transparent 22%),
        #F7F9FC;
    color: #111827;
}

.block-container {
    padding-top: 2.2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 4rem;
    max-width: 1600px;
}

.titulo-pagina {
    font-size: 38px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: -0.8px;
    color: #111827;
    margin-bottom: 10px;
}

.subtitulo-pagina {
    font-size: 16px;
    line-height: 1.5;
    color: #697386;
    margin-bottom: 28px;
}

.titulo-secao {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 22px;
    font-weight: 750;
    color: #111827;
    margin-top: 10px;
    margin-bottom: 20px;
}

.titulo-secao .icone {
    color: #635BFF;
    font-size: 22px;
}

hr {
    border: none !important;
    border-top: 1px solid #E5E7EB !important;
    margin-top: 28px !important;
    margin-bottom: 28px !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    border-radius: 10px;
    min-height: 44px;
    font-weight: 700;
    font-size: 14px;
    border: 1px solid #151A24;
    background: linear-gradient(180deg, #171C27 0%, #10141D 100%);
    color: white !important;
    box-shadow: 0 2px 5px rgba(16, 24, 40, 0.14);
    transition: all 0.15s ease;
}

/* Texto e ícones internos dos botões */
div.stButton > button *,
div.stFormSubmitButton > button * {
    color: white !important;
}

/* Mouse sobre o botão */
div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    border-color: #635BFF;
    color: white !important;
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(16, 24, 40, 0.18);
}

/* Garante branco também durante o hover */
div.stButton > button:hover *,
div.stFormSubmitButton > button:hover * {
    color: white !important;
}


/* CARD DO DEPARTAMENTO - estilizado pela key do container */
div[class*="st-key-dept_card_"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08) !important;
    padding: 22px 24px !important;
    margin-top: 8px !important;
    margin-bottom: 18px !important;
}

div[class*="st-key-dept_card_"] > div {
    background: transparent !important;
}


[data-testid="stVerticalBlockBorderWrapper"] h3 {
    font-size: 23px !important;
    line-height: 1.2 !important;
    font-weight: 800 !important;
    color: #111827 !important;
    letter-spacing: -0.3px;
    margin-bottom: 6px !important;
}

[data-testid="stCaptionContainer"] {
    color: #7B8495 !important;
    font-size: 13px !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #4B5565;
    font-size: 14px;
}

[data-testid="stMarkdownContainer"] a {
    color: #4F6EF7;
    text-decoration: none;
}

[data-testid="stMarkdownContainer"] a:hover {
    text-decoration: underline;
}

div[data-testid="stAlert"] {
    border-radius: 10px;
    border: none;
    min-height: 44px;
    display: flex;
    align-items: center;
}

[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #E2E7EF;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}

div[data-baseweb="input"] > div {
    border-radius: 9px !important;
    background: #FFFFFF !important;
}

label {
    color: #344054 !important;
    font-weight: 600 !important;
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

.rodape-sobreaviso {
    text-align: center;
    color: #7B8495;
    font-size: 13px;
    padding-top: 56px;
    padding-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    '<div class="titulo-pagina">Departamentos</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-pagina">'
    'Cadastre e gerencie os departamentos do sistema.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CONTROLE DE ESTADO
# ============================================================

if "modo_departamento" not in st.session_state:
    st.session_state.modo_departamento = None

if "id_departamento_edicao" not in st.session_state:
    st.session_state.id_departamento_edicao = None


# ============================================================
# EMPRESAS
# ============================================================

try:
    empresas = listar_empresas(apenas_ativas=True)
except Exception as erro:
    st.error(f"Erro ao carregar empresas: {erro}")
    empresas = []

mapa_empresas = {
    e[0]: e[1]
    for e in empresas
}


try:
    gestores = listar_gestores()
except Exception as erro:
    st.error(
        f"Erro ao carregar gestores: {erro}"
    )
    gestores = []


def gestores_por_empresa(id_empresa):
    return [
        g for g in gestores
        if g[2] == id_empresa
    ]


# ============================================================
# NOVO DEPARTAMENTO
# ============================================================

col_botao, _ = st.columns([1, 5])

with col_botao:
    if st.button(
        "➕ Novo Departamento",
        use_container_width=True
    ):
        st.session_state.modo_departamento = "novo"
        st.session_state.id_departamento_edicao = None


# ============================================================
# FORMULÁRIO DE CADASTRO
# ============================================================

if st.session_state.modo_departamento == "novo":

    st.markdown("### Novo Departamento")

    with st.container(
        border=True,
        key="novo_departamento_card"
    ):

        if not mapa_empresas:

            st.warning(
                "Cadastre pelo menos uma empresa ativa "
                "antes de cadastrar departamentos."
            )

            id_empresa = None
            id_gestor = None

        else:

            id_empresa = st.selectbox(
                "Empresa",
                options=list(mapa_empresas.keys()),
                format_func=lambda x: mapa_empresas[x],
                key="novo_departamento_empresa"
            )

            gestores_filtrados = gestores_por_empresa(
                id_empresa
            )

            mapa_gestores = {
                g[0]: g[1]
                for g in gestores_filtrados
            }

            opcoes_gestor = [None] + list(
                mapa_gestores.keys()
            )

            id_gestor = st.selectbox(
                "Gestor do Departamento",
                options=opcoes_gestor,
                format_func=lambda x: (
                    "Sem gestor"
                    if x is None
                    else mapa_gestores[x]
                ),
                key="novo_departamento_gestor"
            )

            if not gestores_filtrados:
                st.caption(
                    "Não há gestores ativos cadastrados "
                    "para esta empresa."
                )

        nome = st.text_input(
            "Nome do Departamento",
            key="novo_departamento_nome"
        )

        col1, col2 = st.columns(2)

        with col1:
            email_1 = st.text_input(
                "E-mail Responsável 1",
                key="novo_departamento_email1"
            )

        with col2:
            email_2 = st.text_input(
                "E-mail Responsável 2",
                key="novo_departamento_email2"
            )

        col_salvar, col_cancelar = st.columns(
            [1, 1]
        )

        with col_salvar:
            salvar = st.button(
                "Salvar",
                key="salvar_novo_departamento",
                use_container_width=True
            )

        with col_cancelar:
            cancelar = st.button(
                "Cancelar",
                key="cancelar_novo_departamento",
                use_container_width=True
            )

        if salvar:

            if id_empresa is None:

                st.error(
                    "Informe uma empresa."
                )

            elif not nome.strip():

                st.error(
                    "Informe o nome do departamento."
                )

            else:

                try:

                    id_departamento = cadastrar_departamento(
                        id_empresa=id_empresa,
                        nome_departamento=nome.strip(),
                        email_responsavel_1=(
                            email_1.strip()
                            if email_1
                            else None
                        ),
                        email_responsavel_2=(
                            email_2.strip()
                            if email_2
                            else None
                        ),
                        id_gestor=id_gestor
                    )

                    st.success(
                        f"Departamento cadastrado "
                        f"com sucesso. ID: {id_departamento}"
                    )

                    st.session_state.modo_departamento = None
                    st.rerun()

                except Exception as erro:

                    st.error(
                        f"Erro ao cadastrar departamento: "
                        f"{erro}"
                    )

        if cancelar:

            st.session_state.modo_departamento = None
            st.rerun()


# ============================================================
# LISTAGEM
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="titulo-secao"><span class="icone">🏢</span>Departamentos cadastrados</div>',
    unsafe_allow_html=True
)


try:

    departamentos = listar_departamentos()

except Exception as erro:

    st.error(
        f"Erro ao consultar departamentos: {erro}"
    )

    departamentos = []


if not departamentos:

    st.info(
        "Nenhum departamento cadastrado."
    )

else:

    for departamento in departamentos:

        (
            id_departamento,
            nome_departamento,
            email_responsavel_1,
            email_responsavel_2,
            ativo,
            data_cadastro,
            id_empresa,
            nome_empresa,
            id_gestor,
            nome_gestor,
        ) = departamento

        with st.container(
            border=True,
            key=f"dept_card_{id_departamento}"
        ):

            col_info, col_status, col_editar, col_excluir = st.columns(
                [5, 1.2, 1, 1]
            )

            with col_info:
                st.markdown(f"### {nome_departamento}")
                st.caption(f"ID: {id_departamento}")
                st.write(f"**Empresa:** {nome_empresa}")

                st.write(
                    f"**Gestor:** "
                    f"{nome_gestor or 'Não definido'}"
                )

                if email_responsavel_1:
                    st.write(
                        f"**Responsável 1:** {email_responsavel_1}"
                    )

                if email_responsavel_2:
                    st.write(
                        f"**Responsável 2:** {email_responsavel_2}"
                    )

            with col_status:
                if ativo:
                    st.success("●  Ativo")
                else:
                    st.warning("●  Inativo")

            with col_editar:
                if st.button(
                    "✏️ Editar",
                    key=f"editar_{id_departamento}",
                    use_container_width=True
                ):
                    st.session_state.modo_departamento = "editar"
                    st.session_state.id_departamento_edicao = id_departamento
                    st.rerun()

            with col_excluir:
                if st.button(
                    "🗑️ Excluir",
                    key=f"excluir_{id_departamento}",
                    use_container_width=True
                ):
                    st.session_state.modo_departamento = "excluir"
                    st.session_state.id_departamento_edicao = id_departamento
                    st.rerun()

        if (
            st.session_state.modo_departamento == "editar"
            and st.session_state.id_departamento_edicao == id_departamento
        ):

            st.markdown("### Editar Departamento")

            with st.form(
                f"form_editar_departamento_{id_departamento}"
            ):

                ids_empresas = list(mapa_empresas.keys())

                indice_empresa = (
                    ids_empresas.index(id_empresa)
                    if id_empresa in ids_empresas
                    else 0
                )

                id_empresa_editado = st.selectbox(
                    "Empresa",
                    options=ids_empresas,
                    index=indice_empresa,
                    format_func=lambda x: mapa_empresas[x],
                    key=f"empresa_edicao_{id_departamento}"
                )

                gestores_filtrados_edicao = (
                    gestores_por_empresa(
                        id_empresa_editado
                    )
                )

                mapa_gestores_edicao = {
                    g[0]: g[1]
                    for g in gestores_filtrados_edicao
                }

                opcoes_gestor_edicao = (
                    [None]
                    + list(
                        mapa_gestores_edicao.keys()
                    )
                )

                indice_gestor = (
                    opcoes_gestor_edicao.index(id_gestor)
                    if id_gestor in opcoes_gestor_edicao
                    else 0
                )

                id_gestor_editado = st.selectbox(
                    "Gestor do Departamento",
                    options=opcoes_gestor_edicao,
                    index=indice_gestor,
                    format_func=lambda x: (
                        "Sem gestor"
                        if x is None
                        else mapa_gestores_edicao[x]
                    ),
                    key=f"gestor_edicao_{id_departamento}"
                )

                if not gestores_filtrados_edicao:
                    st.caption(
                        "Não há gestores ativos cadastrados "
                        "para esta empresa."
                    )

                nome_editado = st.text_input(
                    "Nome do Departamento",
                    value=nome_departamento,
                    key=f"nome_edicao_{id_departamento}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    email_1_editado = st.text_input(
                        "E-mail Responsável 1",
                        value=email_responsavel_1 or "",
                        key=f"email1_edicao_{id_departamento}"
                    )

                with col2:
                    email_2_editado = st.text_input(
                        "E-mail Responsável 2",
                        value=email_responsavel_2 or "",
                        key=f"email2_edicao_{id_departamento}"
                    )

                ativo_editado = st.checkbox(
                    "Departamento ativo",
                    value=ativo,
                    key=f"ativo_edicao_{id_departamento}"
                )

                col_salvar, col_cancelar = st.columns(2)

                with col_salvar:
                    salvar_edicao = st.form_submit_button(
                        "Salvar Alterações",
                        use_container_width=True
                    )

                with col_cancelar:
                    cancelar_edicao = st.form_submit_button(
                        "Cancelar",
                        use_container_width=True
                    )

                if salvar_edicao:

                    if not nome_editado.strip():
                        st.error(
                            "Informe o nome do departamento."
                        )

                    else:
                        try:
                            alterado = alterar_departamento(
                                id_departamento=id_departamento,
                                id_empresa=id_empresa_editado,
                                nome_departamento=nome_editado.strip(),
                                email_responsavel_1=(
                                    email_1_editado.strip()
                                    if email_1_editado
                                    else None
                                ),
                                email_responsavel_2=(
                                    email_2_editado.strip()
                                    if email_2_editado
                                    else None
                                ),
                                ativo=ativo_editado,
                                id_gestor=id_gestor_editado
                            )

                            if alterado:
                                st.success(
                                    "Departamento alterado com sucesso."
                                )
                            else:
                                st.warning(
                                    "Nenhum registro foi alterado."
                                )

                            st.session_state.modo_departamento = None
                            st.session_state.id_departamento_edicao = None
                            st.rerun()

                        except Exception as erro:
                            st.error(
                                f"Erro ao alterar departamento: {erro}"
                            )

                if cancelar_edicao:
                    st.session_state.modo_departamento = None
                    st.session_state.id_departamento_edicao = None
                    st.rerun()

        if (
            st.session_state.modo_departamento == "excluir"
            and st.session_state.id_departamento_edicao == id_departamento
        ):

            st.warning(
                f"Tem certeza que deseja excluir "
                f"o departamento **{nome_departamento}**?"
            )

            col_sim, col_nao, _ = st.columns([1, 1, 4])

            with col_sim:
                if st.button(
                    "Sim, excluir",
                    key=f"confirmar_exclusao_{id_departamento}",
                    type="primary",
                    use_container_width=True
                ):
                    try:
                        excluido = excluir_departamento(
                            id_departamento
                        )

                        if excluido:
                            st.success("Departamento excluído.")
                        else:
                            st.warning(
                                "Departamento não encontrado."
                            )

                        st.session_state.modo_departamento = None
                        st.session_state.id_departamento_edicao = None
                        st.rerun()

                    except Exception as erro:
                        st.error(
                            f"Não foi possível excluir: {erro}"
                        )

            with col_nao:
                if st.button(
                    "Cancelar",
                    key=f"cancelar_exclusao_{id_departamento}",
                    use_container_width=True
                ):
                    st.session_state.modo_departamento = None
                    st.session_state.id_departamento_edicao = None
                    st.rerun()


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    '<div class="rodape-sobreaviso">Sobreaviso Automate &nbsp;•&nbsp; Versão 1.0.0</div>',
    unsafe_allow_html=True)