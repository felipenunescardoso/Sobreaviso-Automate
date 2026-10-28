import streamlit as st

from cadastros import (
    listar_empresas,
    listar_departamentos,
    listar_cidades,
    listar_usuarios,
    cadastrar_usuario,
    alterar_usuario,
    alterar_proprio_cadastro,
    alterar_senha,
    excluir_usuario,
    listar_departamentos_gestor,
    adicionar_departamento_gestor,
    remover_departamento_gestor,
    buscar_recebedores,
    cadastrar_recebedores,
    alterar_recebedores,
    excluir_recebedores
)


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

st.set_page_config(
    page_title="Usuários",
    page_icon="👤",
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


/* CARD DO USUÁRIO - estilizado pela key do container */
div[class*="st-key-user_card_"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08) !important;
    padding: 22px 24px !important;
    margin-top: 8px !important;
    margin-bottom: 18px !important;
}

div[class*="st-key-user_card_"] > div {
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
    '<div class="titulo-pagina">Usuários</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-pagina">'
    'Cadastre e gerencie técnicos, gestores e administradores do sistema.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CONTROLE DE ESTADO
# ============================================================

if "modo_usuario" not in st.session_state:
    st.session_state.modo_usuario = None

if "id_usuario_edicao" not in st.session_state:
    st.session_state.id_usuario_edicao = None


usuario_logado = st.session_state.get("usuario") or {}

id_usuario_logado = usuario_logado.get("id_usuario")
perfil_usuario_logado = (
    usuario_logado.get("perfil") or ""
).upper()

eh_tecnico = (
    perfil_usuario_logado == "TECNICO"
)

eh_gestor = (
    perfil_usuario_logado == "GESTOR"
)

eh_admin = (
    perfil_usuario_logado == "ADMIN"
)


# ============================================================
# CARGAS DOS COMBOS
# ============================================================

try:
    empresas = listar_empresas(apenas_ativas=True)
except Exception as erro:
    st.error(f"Erro ao carregar empresas: {erro}")
    empresas = []

try:
    departamentos = listar_departamentos()
except Exception as erro:
    st.error(f"Erro ao carregar departamentos: {erro}")
    departamentos = []

try:
    cidades = listar_cidades()
except Exception as erro:
    st.error(f"Erro ao carregar cidades: {erro}")
    cidades = []


# listar_departamentos retorna:
# id, nome, email1, email2, ativo, data_cadastro,
# id_empresa, nome_empresa, id_gestor, nome_gestor

mapa_empresas = {
    e[0]: e[1]
    for e in empresas
}

departamentos_ativos = [
    d for d in departamentos
    if len(d) < 5 or d[4] is True
]


def departamentos_por_empresa(id_empresa):
    return [
        d for d in departamentos_ativos
        if len(d) > 6 and d[6] == id_empresa
    ]


def buscar_gestor_no_departamento(id_departamento):
    """
    Retorna (id_gestor, nome_gestor) do departamento selecionado.
    Retorna (None, None) quando não houver gestor definido.
    """

    for departamento in departamentos_ativos:

        if departamento[0] == id_departamento:

            id_gestor = (
                departamento[8]
                if len(departamento) > 8
                else None
            )

            nome_gestor = (
                departamento[9]
                if len(departamento) > 9
                else None
            )

            return id_gestor, nome_gestor

    return None, None


ufs = sorted({
    c[2]
    for c in cidades
    if c[2]
})


def cidades_por_uf(uf):
    return [
        c for c in cidades
        if c[2] == uf
    ]


# ============================================================
# NOVO USUÁRIO
# ============================================================

if eh_admin:

    col_botao, _ = st.columns([1, 5])

    with col_botao:
        if st.button(
            "➕ Novo Usuário",
            use_container_width=True
        ):
            st.session_state.modo_usuario = "novo"
            st.session_state.id_usuario_edicao = None


# ============================================================
# CADASTRO DE USUÁRIO
# ============================================================

if st.session_state.modo_usuario == "novo" and eh_admin:

    st.markdown("### Novo Usuário")

    if not mapa_empresas:
        st.warning(
            "Cadastre pelo menos uma empresa ativa antes de cadastrar usuários."
        )

    elif not departamentos_ativos:
        st.warning(
            "Cadastre pelo menos um departamento antes de cadastrar usuários."
        )

    elif not ufs:
        st.warning(
            "Não há cidades cadastradas para selecionar UF e cidade."
        )

    else:

        # Não usamos st.form aqui porque Cidade depende de UF.
        # O container mantém tudo visualmente no mesmo card.
        with st.container(border=True, key="novo_usuario_card"):

            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input(
                    "Nome",
                    key="novo_usuario_nome"
                )

            with col2:
                chapa = st.text_input(
                    "Matricula",
                    key="novo_usuario_chapa"
                )

            col3, col4 = st.columns(2)

            with col3:
                email = st.text_input(
                    "E-mail",
                    key="novo_usuario_email"
                )

            with col4:
                login = st.text_input(
                    "Login",
                    key="novo_usuario_login"
                )

            col5, col6 = st.columns(2)

            with col5:
                senha = st.text_input(
                    "Senha",
                    type="password",
                    key="novo_usuario_senha"
                )

            with col6:
                perfil = st.selectbox(
                    "Perfil",
                    ["TECNICO", "GESTOR", "ADMIN"],
                    key="novo_usuario_perfil"
                )

            id_empresa = st.selectbox(
                "Empresa",
                options=list(mapa_empresas.keys()),
                format_func=lambda x: mapa_empresas[x],
                key="novo_usuario_empresa"
            )

            departamentos_filtrados = departamentos_por_empresa(id_empresa)

            mapa_departamentos = {
                d[0]: d[1]
                for d in departamentos_filtrados
            }

            if not mapa_departamentos:
                st.warning(
                    "Não há departamentos ativos cadastrados para esta empresa."
                )
                id_departamento = None
            else:
                id_departamento = st.selectbox(
                    "Departamento",
                    options=list(mapa_departamentos.keys()),
                    format_func=lambda x: mapa_departamentos[x],
                    key="novo_usuario_departamento"
                )

            # ========================================================
            # GESTOR AUTOMÁTICO PELO DEPARTAMENTO
            # ========================================================

            id_gestor = None
            nome_gestor_departamento = None

            if id_departamento is not None:

                (
                    id_gestor_departamento,
                    nome_gestor_departamento
                ) = buscar_gestor_no_departamento(
                    id_departamento
                )

                if perfil == "ADMIN":

                    id_gestor = None

                    st.info(
                        "Perfil ADMIN não exige gestor."
                    )

                else:

                    id_gestor = id_gestor_departamento

                    if id_gestor is not None:

                        st.info(
                            f"Gestor responsável: "
                            f"{nome_gestor_departamento}"
                        )

                    else:

                        st.warning(
                            "O departamento selecionado não possui "
                            "gestor definido. Técnicos e gestores "
                            "precisam possuir gestor."
                        )

            # ========================================================
            # UF / CIDADE - abaixo do departamento e dependentes
            # ========================================================

            col7, col8 = st.columns(2)

            with col7:
                uf = st.selectbox(
                    "UF",
                    options=ufs,
                    key="novo_usuario_uf"
                )

            cidades_filtradas = cidades_por_uf(uf)

            mapa_cidades = {
                c[0]: c[1]
                for c in cidades_filtradas
            }

            with col8:
                id_cidade = st.selectbox(
                    "Cidade",
                    options=list(mapa_cidades.keys()),
                    format_func=lambda x: mapa_cidades[x],
                    key="novo_usuario_cidade"
                )

            # ========================================================
            # DEPARTAMENTOS GERENCIADOS
            # ========================================================

            departamentos_gestor = []

            if perfil == "GESTOR":
                departamentos_gestor = st.multiselect(
                    "Departamentos que este usuário gerencia",
                    options=list(mapa_departamentos.keys()),
                    format_func=lambda x: mapa_departamentos[x],
                    key="novo_usuario_departamentos_gestor"
                )

            # ========================================================
            # RECEBEDORES DO SOBREAVISO
            # ========================================================

            emails_recebedores = st.text_input(
                "Gestores que receberão o sobreaviso",
                placeholder="gestor1@empresa.com;gestor2@empresa.com",
                help=(
                    "Informe somente os e-mails adicionais. "
                    "O próprio funcionário receberá pelo e-mail cadastrado acima. "
                    "Separe vários endereços por ponto e vírgula (;)."
                ),
                key="novo_usuario_recebedores"
            )

            col_salvar, col_cancelar = st.columns(2)

            with col_salvar:
                salvar = st.button(
                    "Salvar",
                    key="salvar_novo_usuario",
                    use_container_width=True
                )

            with col_cancelar:
                cancelar = st.button(
                    "Cancelar",
                    key="cancelar_novo_usuario",
                    use_container_width=True
                )

            if salvar:

                if id_departamento is None:
                    st.error("Informe um departamento para a empresa selecionada.")

                elif not nome.strip():
                    st.error("Informe o nome do usuário.")

                elif not email.strip():
                    st.error("Informe o e-mail.")

                elif not login.strip():
                    st.error("Informe o login.")

                elif not senha:
                    st.error("Informe a senha.")

                elif (
                    perfil != "ADMIN"
                    and id_gestor is None
                ):
                    st.error(
                        "O departamento selecionado não possui gestor. "
                        "Defina o gestor do departamento antes de "
                        "cadastrar um TÉCNICO ou GESTOR."
                    )

                else:
                    try:

                        id_usuario = cadastrar_usuario(
                            id_empresa=id_empresa,
                            id_departamento=id_departamento,
                            nome=nome.strip(),
                            chapa=chapa.strip() if chapa else None,
                            email=email.strip(),
                            login=login.strip(),
                            senha=senha,
                            perfil=perfil,
                            id_cidade=id_cidade,
                            uf=uf,
                            id_gestor=id_gestor,
                            departamentos_gestor=departamentos_gestor
                        )

                        if emails_recebedores.strip():
                            cadastrar_recebedores(
                                id_usuario=id_usuario,
                                emails=emails_recebedores.strip()
                            )

                        st.success(
                            f"Usuário cadastrado com sucesso. ID: {id_usuario}"
                        )

                        st.session_state.modo_usuario = None
                        st.rerun()

                    except Exception as erro:
                        st.error(
                            f"Erro ao cadastrar usuário: {erro}"
                        )

            if cancelar:
                st.session_state.modo_usuario = None
                st.rerun()


# ============================================================
# LISTAGEM
# ============================================================

st.markdown("---")

st.markdown(
    (
        '<div class="titulo-secao"><span class="icone">👤</span>Meu cadastro</div>'
        if eh_tecnico
        else (
            '<div class="titulo-secao"><span class="icone">👤</span>Minha equipe</div>'
            if eh_gestor
            else '<div class="titulo-secao"><span class="icone">👤</span>Usuários cadastrados</div>'
        )
    ),
    unsafe_allow_html=True
)


try:
    usuarios = listar_usuarios()

    if eh_tecnico:
        usuarios = [
            usuario
            for usuario in usuarios
            if usuario[0] == id_usuario_logado
        ]

    elif eh_gestor:

        # listar_usuarios retorna id_gestor na posição 15.
        # Monta em memória a hierarquia abaixo do gestor,
        # incluindo níveis indiretos.
        ids_permitidos = {id_usuario_logado}

        alterou = True

        while alterou:
            alterou = False

            for usuario in usuarios:
                id_usuario_item = usuario[0]
                id_gestor_item = usuario[15]

                if (
                    id_gestor_item in ids_permitidos
                    and id_usuario_item not in ids_permitidos
                ):
                    ids_permitidos.add(id_usuario_item)
                    alterou = True

        usuarios = [
            usuario
            for usuario in usuarios
            if usuario[0] in ids_permitidos
        ]

except Exception as erro:
    st.error(f"Erro ao consultar usuários: {erro}")
    usuarios = []


if not usuarios:

    st.info("Nenhum usuário cadastrado.")

else:

    for usuario in usuarios:

        (
            id_usuario,
            nome,
            chapa,
            email,
            login,
            perfil,
            ativo,
            id_departamento,
            nome_departamento,
            id_cidade,
            nome_cidade,
            uf,
            data_cadastro,
            id_empresa,
            nome_empresa,
            id_gestor,
            nome_gestor
        ) = usuario

        with st.container(
            border=True,
            key=f"user_card_{id_usuario}"
        ):

            if eh_tecnico or eh_gestor:
                col_info, col_perfil, col_status, col_senha, col_editar = st.columns(
                    [5.6, 1.1, 1.1, 1, 1]
                )
                col_excluir = None
            else:
                col_info, col_perfil, col_status, col_senha, col_editar, col_excluir = st.columns(
                    [4.5, 1.1, 1.1, 1, 1, 1]
                )

            with col_info:

                st.markdown(
                    f"### {nome}"
                )

                st.caption(
                    f"ID: {id_usuario}  •  Matricula: {chapa or '-'}"
                )

                st.write(
                    f"**Empresa:** {nome_empresa}"
                )

                st.write(
                    f"**Departamento:** {nome_departamento}"
                )

                if nome_cidade and uf:
                    st.write(
                        f"**Cidade:** {nome_cidade} / {uf}"
                    )

                st.write(
                    f"**E-mail:** {email}"
                )

                try:
                    recebedores_usuario = buscar_recebedores(
                        id_usuario
                    )

                    if (
                        recebedores_usuario
                        and recebedores_usuario[3]
                    ):
                        st.write(
                            f"**Recebedores do sobreaviso:** "
                            f"{recebedores_usuario[2]}"
                        )
                except Exception:
                    pass

                if perfil == "GESTOR":
                    try:
                        vinculos = listar_departamentos_gestor(
                            id_usuario
                        )

                        if vinculos:
                            nomes = ", ".join(
                                v[3] for v in vinculos
                            )

                            st.write(
                                f"**Gerencia:** {nomes}"
                            )

                    except Exception:
                        pass

                if nome_gestor:
                    st.write(
                        f"**Gestor:** {nome_gestor}"
                    )

                st.caption(
                    f"Login: {login}"
                )

            with col_perfil:
                st.info(perfil.title())

            with col_status:

                if ativo:
                    st.success("●  Ativo")
                else:
                    st.warning("●  Inativo")

            with col_senha:

                if st.button(
                    "🔑 Senha",
                    key=f"senha_{id_usuario}",
                    use_container_width=True
                ):
                    st.session_state.modo_usuario = "senha"
                    st.session_state.id_usuario_edicao = id_usuario
                    st.rerun()

            with col_editar:

                if st.button(
                    "✏️ Editar",
                    key=f"editar_{id_usuario}",
                    use_container_width=True
                ):
                    st.session_state.modo_usuario = "editar"
                    st.session_state.id_usuario_edicao = id_usuario
                    st.rerun()

            if eh_admin and col_excluir is not None:

                with col_excluir:

                    if st.button(
                        "🗑️ Excluir",
                        key=f"excluir_{id_usuario}",
                        use_container_width=True
                    ):
                        st.session_state.modo_usuario = "excluir"
                        st.session_state.id_usuario_edicao = id_usuario
                        st.rerun()


        # ========================================================
        # ALTERAÇÃO DE SENHA INLINE
        # ========================================================

        if (
            st.session_state.modo_usuario == "senha"
            and st.session_state.id_usuario_edicao == id_usuario
        ):

            if (
                eh_tecnico
                and id_usuario != id_usuario_logado
            ):
                st.error(
                    "Você só pode alterar a própria senha."
                )
                st.session_state.modo_usuario = None
                st.session_state.id_usuario_edicao = None
                st.stop()

            st.markdown(
                f"### Alterar Senha - {nome}"
            )

            with st.form(
                f"form_senha_usuario_{id_usuario}"
            ):

                nova_senha = st.text_input(
                    "Nova Senha",
                    type="password",
                    key=f"nova_senha_{id_usuario}"
                )

                confirmar_senha = st.text_input(
                    "Confirmar Nova Senha",
                    type="password",
                    key=f"confirmar_senha_{id_usuario}"
                )

                col_salvar, col_cancelar = st.columns(2)

                with col_salvar:
                    salvar_senha = st.form_submit_button(
                        "Alterar Senha",
                        use_container_width=True
                    )

                with col_cancelar:
                    cancelar_senha = st.form_submit_button(
                        "Cancelar",
                        use_container_width=True
                    )

                if salvar_senha:

                    if not nova_senha:

                        st.error(
                            "Informe a nova senha."
                        )

                    elif nova_senha != confirmar_senha:

                        st.error(
                            "As senhas não conferem."
                        )

                    else:

                        try:

                            alterado = alterar_senha(
                                id_usuario,
                                nova_senha
                            )

                            if alterado:

                                st.success(
                                    "Senha alterada com sucesso."
                                )

                            else:

                                st.warning(
                                    "Usuário não encontrado."
                                )

                            st.session_state.modo_usuario = None
                            st.session_state.id_usuario_edicao = None

                            st.rerun()

                        except Exception as erro:

                            st.error(
                                f"Erro ao alterar senha: {erro}"
                            )

                if cancelar_senha:

                    st.session_state.modo_usuario = None
                    st.session_state.id_usuario_edicao = None
                    st.rerun()


        # ========================================================
        # EDIÇÃO INLINE
        # ========================================================

        if (
            st.session_state.modo_usuario == "editar"
            and st.session_state.id_usuario_edicao == id_usuario
        ):

            if (
                eh_tecnico
                and id_usuario != id_usuario_logado
            ):
                st.error(
                    "Você só pode editar o próprio cadastro."
                )
                st.session_state.modo_usuario = None
                st.session_state.id_usuario_edicao = None
                st.stop()

            if eh_tecnico:

                st.markdown(
                    f"### Editar Meu Cadastro - {nome}"
                )

                with st.container(
                    border=True,
                    key=f"editar_meu_cadastro_{id_usuario}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:
                        nome_editado = st.text_input(
                            "Nome",
                            value=nome,
                            key=f"tecnico_nome_{id_usuario}"
                        )

                    with col2:
                        chapa_editada = st.text_input(
                            "Matricula",
                            value=chapa or "",
                            key=f"tecnico_chapa_{id_usuario}"
                        )

                    email_editado = st.text_input(
                        "E-mail",
                        value=email,
                        key=f"tecnico_email_{id_usuario}"
                    )

                    st.markdown("#### Dados não editáveis")

                    col3, col4 = st.columns(2)

                    with col3:
                        st.text_input(
                            "Login",
                            value=login,
                            disabled=True,
                            key=f"tecnico_login_{id_usuario}"
                        )

                    with col4:
                        st.text_input(
                            "Perfil",
                            value=perfil,
                            disabled=True,
                            key=f"tecnico_perfil_{id_usuario}"
                        )

                    col5, col6 = st.columns(2)

                    with col5:
                        st.text_input(
                            "Empresa",
                            value=nome_empresa or "",
                            disabled=True,
                            key=f"tecnico_empresa_{id_usuario}"
                        )

                    with col6:
                        st.text_input(
                            "Departamento",
                            value=nome_departamento or "",
                            disabled=True,
                            key=f"tecnico_departamento_{id_usuario}"
                        )

                    col7, col8 = st.columns(2)

                    with col7:
                        st.text_input(
                            "Gestor",
                            value=nome_gestor or "",
                            disabled=True,
                            key=f"tecnico_gestor_{id_usuario}"
                        )

                    with col8:
                        st.text_input(
                            "Cidade / UF",
                            value=(
                                f"{nome_cidade} / {uf}"
                                if nome_cidade and uf
                                else ""
                            ),
                            disabled=True,
                            key=f"tecnico_cidade_{id_usuario}"
                        )

                    col_salvar, col_cancelar = st.columns(2)

                    with col_salvar:
                        salvar_proprio = st.button(
                            "Salvar Alterações",
                            key=f"salvar_proprio_{id_usuario}",
                            use_container_width=True
                        )

                    with col_cancelar:
                        cancelar_proprio = st.button(
                            "Cancelar",
                            key=f"cancelar_proprio_{id_usuario}",
                            use_container_width=True
                        )

                    if salvar_proprio:

                        if not nome_editado.strip():
                            st.error(
                                "Informe o nome."
                            )

                        elif not email_editado.strip():
                            st.error(
                                "Informe o e-mail."
                            )

                        else:

                            try:

                                alterado = alterar_proprio_cadastro(
                                    id_usuario=id_usuario_logado,
                                    nome=nome_editado.strip(),
                                    chapa=(
                                        chapa_editada.strip()
                                        if chapa_editada
                                        else None
                                    ),
                                    email=email_editado.strip()
                                )

                                if alterado:
                                    st.success(
                                        "Cadastro alterado com sucesso."
                                    )
                                else:
                                    st.warning(
                                        "Nenhum registro foi alterado."
                                    )

                                st.session_state.modo_usuario = None
                                st.session_state.id_usuario_edicao = None
                                st.rerun()

                            except Exception as erro:

                                st.error(
                                    f"Erro ao alterar cadastro: {erro}"
                                )

                    if cancelar_proprio:

                        st.session_state.modo_usuario = None
                        st.session_state.id_usuario_edicao = None
                        st.rerun()

                # Não executa a edição administrativa abaixo.
                continue

            try:
                vinculos_atuais = listar_departamentos_gestor(
                    id_usuario
                )

                ids_gestor_atuais = [
                    v[2]
                    for v in vinculos_atuais
                ]

            except Exception:
                ids_gestor_atuais = []

            try:
                recebedores_atual = buscar_recebedores(
                    id_usuario
                )

                if recebedores_atual:
                    emails_recebedores_atual = (
                        recebedores_atual[2] or ""
                    )
                else:
                    emails_recebedores_atual = ""

            except Exception:
                recebedores_atual = None
                emails_recebedores_atual = ""

            st.markdown(
                f"### Editar Usuário - {nome}"
            )

            with st.container(
                border=True,
                key=f"editar_usuario_card_{id_usuario}"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    nome_editado = st.text_input(
                        "Nome",
                        value=nome,
                        key=f"editar_nome_{id_usuario}"
                    )

                with col2:
                    chapa_editada = st.text_input(
                        "Matricula",
                        value=chapa or "",
                        key=f"editar_chapa_{id_usuario}"
                    )

                col3, col4 = st.columns(2)

                with col3:
                    email_editado = st.text_input(
                        "E-mail",
                        value=email,
                        key=f"editar_email_{id_usuario}"
                    )

                with col4:
                    login_editado = st.text_input(
                        "Login",
                        value=login,
                        key=f"editar_login_{id_usuario}"
                    )

                ids_empresas = list(
                    mapa_empresas.keys()
                )

                indice_empresa = (
                    ids_empresas.index(id_empresa)
                    if id_empresa in ids_empresas
                    else 0
                )

                id_empresa_editada = st.selectbox(
                    "Empresa",
                    options=ids_empresas,
                    index=indice_empresa,
                    format_func=lambda x: mapa_empresas[x],
                    key=f"editar_empresa_{id_usuario}"
                )

                departamentos_filtrados_edicao = (
                    departamentos_por_empresa(
                        id_empresa_editada
                    )
                )

                mapa_departamentos_edicao = {
                    d[0]: d[1]
                    for d in departamentos_filtrados_edicao
                }

                ids_departamentos = list(
                    mapa_departamentos_edicao.keys()
                )

                if ids_departamentos:

                    indice_departamento = (
                        ids_departamentos.index(id_departamento)
                        if id_departamento in ids_departamentos
                        else 0
                    )

                    id_departamento_editado = st.selectbox(
                        "Departamento",
                        options=ids_departamentos,
                        index=indice_departamento,
                        format_func=lambda x: mapa_departamentos_edicao[x],
                        key=f"editar_departamento_{id_usuario}"
                    )

                else:

                    st.warning(
                        "Não há departamentos ativos cadastrados "
                        "para esta empresa."
                    )

                    id_departamento_editado = None

                # ====================================================
                # GESTOR AUTOMÁTICO PELO DEPARTAMENTO
                # ====================================================

                id_gestor_editado = None
                nome_gestor_departamento_editado = None

                if id_departamento_editado is not None:

                    (
                        id_gestor_departamento_editado,
                        nome_gestor_departamento_editado
                    ) = buscar_gestor_no_departamento(
                        id_departamento_editado
                    )

                col5, col6 = st.columns(2)

                with col5:

                    indice_uf = (
                        ufs.index(uf)
                        if uf in ufs
                        else 0
                    )

                    uf_editada = st.selectbox(
                        "UF",
                        options=ufs,
                        index=indice_uf,
                        key=f"editar_usuario_uf_{id_usuario}"
                    )

                cidades_filtradas = cidades_por_uf(
                    uf_editada
                )

                mapa_cidades_edicao = {
                    c[0]: c[1]
                    for c in cidades_filtradas
                }

                ids_cidades = list(
                    mapa_cidades_edicao.keys()
                )

                indice_cidade = (
                    ids_cidades.index(id_cidade)
                    if id_cidade in ids_cidades
                    else 0
                )

                with col6:

                    id_cidade_editada = st.selectbox(
                        "Cidade",
                        options=ids_cidades,
                        index=indice_cidade,
                        format_func=lambda x: mapa_cidades_edicao[x],
                        key=f"editar_usuario_cidade_{id_usuario}"
                    )

                col7, col8 = st.columns(2)

                with col7:

                    perfil_editado = st.selectbox(
                        "Perfil",
                        ["TECNICO", "GESTOR", "ADMIN"],
                        index=[
                            "TECNICO",
                            "GESTOR",
                            "ADMIN"
                        ].index(perfil),
                        key=f"editar_perfil_{id_usuario}"
                    )

                with col8:

                    ativo_editado = st.checkbox(
                        "Usuário ativo",
                        value=ativo,
                        key=f"editar_ativo_{id_usuario}"
                    )

                if perfil_editado == "ADMIN":

                    id_gestor_editado = None

                    st.info(
                        "Perfil ADMIN não exige gestor."
                    )

                else:

                    id_gestor_editado = (
                        id_gestor_departamento_editado
                        if id_departamento_editado is not None
                        else None
                    )

                    if id_gestor_editado is not None:

                        if id_gestor_editado == id_usuario:

                            st.warning(
                                "O usuário selecionado está definido como "
                                "gestor do próprio departamento. Como o perfil "
                                "GESTOR também precisa possuir gestor, escolha "
                                "um departamento cujo gestor seja outro usuário."
                            )

                        else:

                            st.info(
                                f"Gestor responsável: "
                                f"{nome_gestor_departamento_editado}"
                            )

                    else:

                        st.warning(
                            "O departamento selecionado não possui "
                            "gestor definido. Técnicos e gestores "
                            "precisam possuir gestor."
                        )

                departamentos_gestor = []

                if perfil_editado == "GESTOR":

                    defaults_gestor = [
                        id_depto
                        for id_depto in ids_gestor_atuais
                        if id_depto
                        in mapa_departamentos_edicao
                    ]

                    departamentos_gestor = st.multiselect(
                        "Departamentos que este usuário gerencia",
                        options=list(
                            mapa_departamentos_edicao.keys()
                        ),
                        default=defaults_gestor,
                        format_func=lambda x:
                            mapa_departamentos_edicao[x],
                        key=f"editar_departamentos_gestor_{id_usuario}"
                    )

                emails_recebedores = st.text_input(
                    "Gestores que receberão o sobreaviso",
                    value=emails_recebedores_atual,
                    placeholder=(
                        "gestor1@empresa.com;"
                        "gestor2@empresa.com"
                    ),
                    help=(
                        "Informe somente os e-mails adicionais. "
                        "O próprio funcionário já receberá pelo "
                        "e-mail cadastrado. Separe vários "
                        "endereços por ponto e vírgula (;)."
                    ),
                    key=f"editar_recebedores_{id_usuario}"
                )

                col_salvar, col_cancelar = st.columns(2)

                with col_salvar:

                    salvar_edicao = st.button(
                        "Salvar Alterações",
                        key=f"salvar_edicao_usuario_{id_usuario}",
                        use_container_width=True
                    )

                with col_cancelar:

                    cancelar_edicao = st.button(
                        "Cancelar",
                        key=f"cancelar_edicao_usuario_{id_usuario}",
                        use_container_width=True
                    )

                if salvar_edicao:

                    if id_departamento_editado is None:

                        st.error(
                            "Informe um departamento para "
                            "a empresa selecionada."
                        )

                    elif not nome_editado.strip():

                        st.error(
                            "Informe o nome do usuário."
                        )

                    elif not email_editado.strip():

                        st.error(
                            "Informe o e-mail."
                        )

                    elif not login_editado.strip():

                        st.error(
                            "Informe o login."
                        )

                    elif (
                        perfil_editado != "ADMIN"
                        and id_gestor_editado is None
                    ):

                        st.error(
                            "O departamento selecionado não possui gestor. "
                            "Defina o gestor do departamento antes de salvar."
                        )

                    elif (
                        perfil_editado != "ADMIN"
                        and id_gestor_editado == id_usuario
                    ):

                        st.error(
                            "O usuário não pode ser o próprio gestor."
                        )

                    else:

                        try:

                            alterado = alterar_usuario(
                                id_usuario=id_usuario,
                                id_empresa=id_empresa_editada,
                                id_departamento=id_departamento_editado,
                                nome=nome_editado.strip(),
                                chapa=(
                                    chapa_editada.strip()
                                    if chapa_editada
                                    else None
                                ),
                                email=email_editado.strip(),
                                login=login_editado.strip(),
                                perfil=perfil_editado,
                                id_cidade=id_cidade_editada,
                                uf=uf_editada,
                                id_gestor=id_gestor_editado,
                                ativo=ativo_editado
                            )

                            desejados = (
                                set(departamentos_gestor)
                                if perfil_editado == "GESTOR"
                                else set()
                            )

                            atuais = set(
                                ids_gestor_atuais
                            )

                            adicionar = (
                                desejados - atuais
                            )

                            remover = (
                                atuais - desejados
                            )

                            for id_depto in adicionar:

                                adicionar_departamento_gestor(
                                    id_usuario,
                                    id_depto
                                )

                            for id_depto in remover:

                                remover_departamento_gestor(
                                    id_usuario,
                                    id_depto
                                )

                            emails_recebedores = (
                                emails_recebedores.strip()
                            )

                            if recebedores_atual:

                                if emails_recebedores:

                                    alterar_recebedores(
                                        id_usuario=id_usuario,
                                        emails=emails_recebedores,
                                        ativo=True
                                    )

                                else:

                                    excluir_recebedores(
                                        id_usuario
                                    )

                            elif emails_recebedores:

                                cadastrar_recebedores(
                                    id_usuario=id_usuario,
                                    emails=emails_recebedores
                                )

                            if alterado:

                                st.success(
                                    "Usuário alterado com sucesso."
                                )

                            else:

                                st.success(
                                    "Vínculos do gestor atualizados "
                                    "com sucesso."
                                )

                            st.session_state.modo_usuario = None
                            st.session_state.id_usuario_edicao = None

                            st.rerun()

                        except Exception as erro:

                            st.error(
                                f"Erro ao alterar usuário: {erro}"
                            )

                if cancelar_edicao:

                    st.session_state.modo_usuario = None
                    st.session_state.id_usuario_edicao = None
                    st.rerun()


        # ========================================================
        # EXCLUSÃO INLINE
        # ========================================================

        if (
            eh_admin
            and st.session_state.modo_usuario == "excluir"
            and st.session_state.id_usuario_edicao == id_usuario
        ):

            st.warning(
                f"Tem certeza que deseja excluir "
                f"o usuário **{nome}**?"
            )

            col_sim, col_nao, _ = st.columns(
                [1, 1, 4]
            )

            with col_sim:

                if st.button(
                    "Sim, excluir",
                    key=f"confirmar_exclusao_usuario_{id_usuario}",
                    type="primary",
                    use_container_width=True
                ):

                    try:

                        try:
                            vinculos = (
                                listar_departamentos_gestor(
                                    id_usuario
                                )
                            )

                            for vinculo in vinculos:

                                remover_departamento_gestor(
                                    id_usuario,
                                    vinculo[2]
                                )

                        except Exception:
                            pass

                        try:
                            excluir_recebedores(
                                id_usuario
                            )
                        except Exception:
                            pass

                        excluido = excluir_usuario(
                            id_usuario
                        )

                        if excluido:

                            st.success(
                                "Usuário excluído."
                            )

                        else:

                            st.warning(
                                "Usuário não encontrado."
                            )

                        st.session_state.modo_usuario = None
                        st.session_state.id_usuario_edicao = None
                        st.rerun()

                    except Exception as erro:

                        st.error(
                            f"Não foi possível excluir: {erro}"
                        )

            with col_nao:

                if st.button(
                    "Cancelar",
                    key=f"cancelar_exclusao_usuario_{id_usuario}",
                    use_container_width=True
                ):

                    st.session_state.modo_usuario = None
                    st.session_state.id_usuario_edicao = None
                    st.rerun()


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    '<div class="rodape-sobreaviso">Sobreaviso Automate &nbsp;•&nbsp; Versão 1.0.0</div>',
    unsafe_allow_html=True
)