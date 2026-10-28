import streamlit as st
from datetime import datetime

from cadastros import (
    listar_departamentos,
    listar_usuarios_departamento,
    listar_escalas,
    cadastrar_escala,
    alterar_escala,
    listar_historico_escala,
    excluir_escala
)


from escalas_permissoes import usuarios_permitidos

st.set_page_config(
    page_title="Escalas",
    page_icon="📅",
    layout="wide"
)

usuario_logado = st.session_state.get("usuario")
if not usuario_logado:
    st.error("Acesso negado: faça login para gerenciar escalas.")
    st.stop()
try:
    ids_permitidos = usuarios_permitidos(usuario_logado)
except (PermissionError, ValueError, TypeError) as erro:
    st.error(str(erro))
    st.stop()
perfil_logado = str(usuario_logado["perfil"]).upper()
pode_gerenciar = perfil_logado in ("ADMIN", "GESTOR")


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================



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

div.stButton > button *,
div.stFormSubmitButton > button * {
    color: white !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    border-color: #635BFF;
    color: white !important;
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(16, 24, 40, 0.18);
}

div.stButton > button:hover *,
div.stFormSubmitButton > button:hover * {
    color: white !important;
}

/* CARD DA ESCALA */
div[class*="st-key-escala_card_"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08) !important;
    padding: 22px 24px !important;
    margin-top: 8px !important;
    margin-bottom: 18px !important;
}

div[class*="st-key-escala_card_"] > div {
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

div[data-testid="stAlert"] {
    border-radius: 10px;
    border: none;
    min-height: 44px;
    display: flex;
    align-items: center;
}

div[data-baseweb="input"] > div {
    border-radius: 9px !important;
}

/* CAMPOS DE DATA */
div[data-testid="stDateInput"] input {
    background-color: #262730 !important;
    color: white !important;
    border-radius: 9px !important;
}

div[data-testid="stDateInput"] > div > div {
    background-color: #262730 !important;
}

div[data-testid="stDateInput"] svg {
    fill: white !important;
    color: white !important;
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
    '<div class="titulo-pagina">Escalas</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-pagina">'
    'Cadastre e gerencie as escalas de sobreaviso dos departamentos.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CONTROLE DE ESTADO
# ============================================================

if "modo_escala" not in st.session_state:
    st.session_state.modo_escala = None

if "id_escala_edicao" not in st.session_state:
    st.session_state.id_escala_edicao = None


# ============================================================
# CARGA DE DEPARTAMENTOS
# ============================================================

try:
    departamentos = listar_departamentos()
except Exception as erro:
    st.error(f"Erro ao carregar departamentos: {erro}")
    departamentos = []


departamentos_ativos = [
    d for d in departamentos
    if len(d) < 5 or d[4] is True
]

mapa_departamentos = {
    d[0]: d[1]
    for d in departamentos_ativos
}


# ============================================================
# NOVA ESCALA
# ============================================================

col_botao, _ = st.columns([1, 5])

with col_botao:
    if pode_gerenciar and st.button(
        "➕ Nova Escala",
        use_container_width=True
    ):
        st.session_state.modo_escala = "novo"
        st.session_state.id_escala_edicao = None


# ============================================================
# CADASTRO
# ============================================================

if st.session_state.modo_escala == "novo" and pode_gerenciar:

    st.markdown("### Nova Escala")

    if not mapa_departamentos:

        st.warning(
            "Cadastre pelo menos um departamento antes de criar escalas."
        )

    else:

        with st.container(
            border=True,
            key="nova_escala_card"
        ):

            # --------------------------------------------------------
            # DEPARTAMENTO
            # --------------------------------------------------------

            id_departamento = st.selectbox(
                "Departamento",
                disabled=not pode_gerenciar,
                options=list(mapa_departamentos.keys()),
                format_func=lambda x: mapa_departamentos[x],
                key="nova_escala_departamento"
            )

            # --------------------------------------------------------
            # USUÁRIOS DO DEPARTAMENTO
            # --------------------------------------------------------

            try:
                usuarios_departamento = listar_usuarios_departamento(
                    id_departamento
                )
                if ids_permitidos is not None:
                    usuarios_departamento = [u for u in usuarios_departamento if u[0] in ids_permitidos]
            except Exception as erro:
                st.error(
                    f"Erro ao carregar usuários do departamento: {erro}"
                )
                usuarios_departamento = []

            mapa_usuarios = {
                u[0]: (
                    f"{u[1]} - {u[2]}"
                    if len(u) > 2 and u[2]
                    else u[1]
                )
                for u in usuarios_departamento
            }

            if not mapa_usuarios:

                st.warning(
                    "Não existem usuários ativos cadastrados neste departamento."
                )

            else:

                id_usuario = st.selectbox(
                    "Usuário",
                    disabled=not pode_gerenciar,
                    options=list(mapa_usuarios.keys()),
                    format_func=lambda x: mapa_usuarios[x],
                    key="nova_escala_usuario"
                )

                # ----------------------------------------------------
                # DATA / HORA INÍCIO
                # ----------------------------------------------------

                col1, col2 = st.columns(2)

                with col1:
                    data_inicio = st.date_input(
                        "Data Início",
                        format="DD/MM/YYYY",
                        key="nova_escala_data_inicio"
                    )

                with col2:
                    hora_inicio = st.time_input(
                        "Hora Início",
                        key="nova_escala_hora_inicio"
                    )

                # ----------------------------------------------------
                # DATA / HORA FIM
                # ----------------------------------------------------

                col3, col4 = st.columns(2)

                with col3:
                    data_fim = st.date_input(
                        "Data Fim",
                        format="DD/MM/YYYY",
                        key="nova_escala_data_fim"
                    )

                with col4:
                    hora_fim = st.time_input(
                        "Hora Fim",
                        key="nova_escala_hora_fim"
                    )

                # ----------------------------------------------------
                # ORDEM / REPLICAÇÃO
                # ----------------------------------------------------

                col5, col6 = st.columns(2)

                with col5:
                    ordem = st.number_input(
                        "Ordem",
                        disabled=not pode_gerenciar,
                        min_value=1,
                        step=1,
                        value=1,
                        key="nova_escala_ordem"
                    )

                with col6:
                    replicacao = st.checkbox(
                        "Replicar escala",
                        disabled=not pode_gerenciar,
                        value=False,
                        key="nova_escala_replicacao"
                    )

                # ----------------------------------------------------
                # BOTÕES
                # ----------------------------------------------------

                col_salvar, col_cancelar = st.columns(2)

                with col_salvar:
                    salvar = st.button(
                        "Salvar",
                        key="salvar_nova_escala",
                        use_container_width=True
                    )

                with col_cancelar:
                    cancelar = st.button(
                        "Cancelar",
                        key="cancelar_nova_escala",
                        use_container_width=True
                    )

                if salvar:

                    data_hora_inicio = datetime.combine(
                        data_inicio,
                        hora_inicio
                    )

                    data_hora_fim = datetime.combine(
                        data_fim,
                        hora_fim
                    )

                    if data_hora_fim <= data_hora_inicio:

                        st.error(
                            "A data/hora final deve ser maior que a data/hora inicial."
                        )

                    else:

                        try:

                            id_escala = cadastrar_escala(
                                id_usuario=id_usuario,
                                data_hora_inicio=data_hora_inicio,
                                data_hora_fim=data_hora_fim,
                                ordem=int(ordem),
                                replicacao=replicacao
                            )

                            st.success(
                                f"Escala cadastrada com sucesso. ID: {id_escala}"
                            )

                            st.session_state.modo_escala = None
                            st.rerun()

                        except Exception as erro:

                            st.error(
                                f"Erro ao cadastrar escala: {erro}"
                            )

                if cancelar:

                    st.session_state.modo_escala = None
                    st.rerun()


# ============================================================
# LISTAGEM
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="titulo-secao"><span class="icone">📅</span>Escalas cadastradas</div>',
    unsafe_allow_html=True
)


try:
    escalas = listar_escalas()
    if ids_permitidos is not None:
        escalas = [e for e in escalas if e[1] in ids_permitidos]
except Exception as erro:
    st.error(
        f"Erro ao consultar escalas: {erro}"
    )
    escalas = []


if not escalas:

    st.info(
        "Nenhuma escala cadastrada."
    )

else:

    for escala in escalas:

        (
            id_escala,
            id_usuario,
            nome_usuario,
            data_hora_inicio,
            data_hora_fim,
            ordem,
            replicacao,
            id_escala_origem,
            data_cadastro
        ) = escala

        with st.container(
            border=True,
            key=f"escala_card_{id_escala}"
        ):

            col_info, col_ordem, col_replica, col_editar, col_excluir = st.columns(
                [5, 1, 1.3, 1, 1]
            )

            with col_info:

                st.markdown(
                    f"### {nome_usuario}"
                )

                st.caption(
                    f"ID Escala: {id_escala}"
                )

                st.write(
                    f"**Início:** "
                    f"{data_hora_inicio.strftime('%d/%m/%Y %H:%M')}"
                )

                st.write(
                    f"**Fim:** "
                    f"{data_hora_fim.strftime('%d/%m/%Y %H:%M')}"
                )

            with col_ordem:

                st.info(
                    f"Ordem {ordem}"
                )

            with col_replica:

                if replicacao:
                    st.success(
                        "●  Replica"
                    )
                else:
                    st.warning(
                        "●  Não replica"
                    )

            with col_editar:

                if st.button(
                    "✏️ Editar",
                    key=f"editar_escala_{id_escala}",
                    use_container_width=True
                ):
                    st.session_state.modo_escala = "editar"
                    st.session_state.id_escala_edicao = id_escala

            if st.button("📜 Histórico", key=f"historico_escala_{id_escala}"):
                st.session_state["historico_escala_id"] = id_escala
            if st.session_state.get("historico_escala_id") == id_escala:
                try:
                    historico = listar_historico_escala(id_escala, usuario_executor=usuario_logado)
                    if not historico:
                        st.caption("Nenhuma alteração auditada até o momento.")
                    for quando, operacao, autor, antes, depois in historico:
                        with st.expander(f"{quando:%d/%m/%Y %H:%M} | {operacao} | {autor or 'SISTEMA'}"):
                            st.write("Antes:", antes)
                            st.write("Depois:", depois)
                except Exception as erro:
                    st.error(f"Histórico indisponível: {erro}")

            with col_excluir:

                if not pode_gerenciar:
                    st.caption("Exclusão restrita")

                if pode_gerenciar and st.button(
                    "🗑️ Excluir",
                    key=f"excluir_escala_{id_escala}",
                    use_container_width=True
                ):
                    st.session_state.modo_escala = "excluir"
                    st.session_state.id_escala_edicao = id_escala


# ============================================================
# ALTERAÇÃO
# ============================================================

if (
    st.session_state.modo_escala == "editar"
    and st.session_state.id_escala_edicao
):

    id_edicao = st.session_state.id_escala_edicao

    escala_edicao = next(
        (
            e for e in escalas
            if e[0] == id_edicao
        ),
        None
    )

    if escala_edicao:

        (
            id_escala,
            id_usuario_atual,
            nome_usuario_atual,
            data_inicio_atual,
            data_fim_atual,
            ordem_atual,
            replicacao_atual,
            id_escala_origem,
            data_cadastro
        ) = escala_edicao

        st.markdown("---")
        st.markdown("### Editar Escala")

        with st.container(
            border=True,
            key=f"editar_escala_card_{id_escala}"
        ):

            # Descobre o departamento atual do usuário
            id_departamento_atual = None

            for departamento in departamentos_ativos:

                try:
                    usuarios_tmp = listar_usuarios_departamento(
                        departamento[0]
                    )
                except Exception:
                    usuarios_tmp = []

                if any(
                    u[0] == id_usuario_atual
                    for u in usuarios_tmp
                ):
                    id_departamento_atual = departamento[0]
                    break

            ids_departamentos = list(
                mapa_departamentos.keys()
            )

            indice_departamento = (
                ids_departamentos.index(id_departamento_atual)
                if id_departamento_atual in ids_departamentos
                else 0
            )

            id_departamento = st.selectbox(
                "Departamento",
                disabled=not pode_gerenciar,
                options=ids_departamentos,
                index=indice_departamento,
                format_func=lambda x: mapa_departamentos[x],
                key=f"editar_escala_departamento_{id_escala}"
            )

            try:
                usuarios_departamento = listar_usuarios_departamento(
                    id_departamento
                )
                if ids_permitidos is not None:
                    usuarios_departamento = [u for u in usuarios_departamento if u[0] in ids_permitidos]
            except Exception as erro:
                st.error(
                    f"Erro ao carregar usuários: {erro}"
                )
                usuarios_departamento = []

            mapa_usuarios = {
                u[0]: (
                    f"{u[1]} - {u[2]}"
                    if len(u) > 2 and u[2]
                    else u[1]
                )
                for u in usuarios_departamento
            }

            ids_usuarios = list(
                mapa_usuarios.keys()
            )

            indice_usuario = (
                ids_usuarios.index(id_usuario_atual)
                if id_usuario_atual in ids_usuarios
                else 0
            )

            if ids_usuarios:

                id_usuario = st.selectbox(
                    "Usuário",
                    disabled=not pode_gerenciar,
                    options=ids_usuarios,
                    index=indice_usuario,
                    format_func=lambda x: mapa_usuarios[x],
                    key=f"editar_escala_usuario_{id_escala}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    data_inicio = st.date_input(
                        "Data Início",
                        value=data_inicio_atual.date(),
                        format="DD/MM/YYYY",
                        key=f"editar_data_inicio_{id_escala}"
                    )

                with col2:
                    hora_inicio = st.time_input(
                        "Hora Início",
                        value=data_inicio_atual.time(),
                        key=f"editar_hora_inicio_{id_escala}"
                    )

                col3, col4 = st.columns(2)

                with col3:
                    data_fim = st.date_input(
                        "Data Fim",
                        value=data_fim_atual.date(),
                        format="DD/MM/YYYY",
                        key=f"editar_data_fim_{id_escala}"
                    )

                with col4:
                    hora_fim = st.time_input(
                        "Hora Fim",
                        value=data_fim_atual.time(),
                        key=f"editar_hora_fim_{id_escala}"
                    )

                col5, col6 = st.columns(2)

                with col5:
                    ordem = st.number_input(
                        "Ordem",
                        disabled=not pode_gerenciar,
                        min_value=1,
                        step=1,
                        value=int(ordem_atual),
                        key=f"editar_ordem_{id_escala}"
                    )

                with col6:
                    replicacao = st.checkbox(
                        "Replicar escala",
                        disabled=not pode_gerenciar,
                        value=replicacao_atual,
                        key=f"editar_replicacao_{id_escala}"
                    )

                col_salvar, col_cancelar = st.columns(2)

                with col_salvar:
                    salvar_edicao = st.button(
                        "Salvar Alterações",
                        key=f"salvar_edicao_escala_{id_escala}",
                        use_container_width=True
                    )

                with col_cancelar:
                    cancelar_edicao = st.button(
                        "Cancelar",
                        key=f"cancelar_edicao_escala_{id_escala}",
                        use_container_width=True
                    )

                if salvar_edicao:

                    data_hora_inicio = datetime.combine(
                        data_inicio,
                        hora_inicio
                    )

                    data_hora_fim = datetime.combine(
                        data_fim,
                        hora_fim
                    )

                    if data_hora_fim <= data_hora_inicio:

                        st.error(
                            "A data/hora final deve ser maior que a data/hora inicial."
                        )

                    else:

                        try:

                            alterado = alterar_escala(
                                usuario_executor=usuario_logado,
                                id_escala=id_escala,
                                id_usuario=id_usuario,
                                data_hora_inicio=data_hora_inicio,
                                data_hora_fim=data_hora_fim,
                                ordem=int(ordem),
                                replicacao=replicacao
                            )

                            if alterado:
                                st.success(
                                    "Escala alterada com sucesso."
                                )
                            else:
                                st.warning(
                                    "Nenhum registro foi alterado."
                                )

                            st.session_state.modo_escala = None
                            st.session_state.id_escala_edicao = None

                            st.rerun()

                        except Exception as erro:

                            st.error(
                                f"Erro ao alterar escala: {erro}"
                            )

                if cancelar_edicao:

                    st.session_state.modo_escala = None
                    st.session_state.id_escala_edicao = None

                    st.rerun()

            else:

                st.warning(
                    "Não existem usuários ativos neste departamento."
                )


# ============================================================
# EXCLUSÃO
# ============================================================

if (
    pode_gerenciar
    and st.session_state.modo_escala == "excluir"
    and st.session_state.id_escala_edicao
):

    id_exclusao = st.session_state.id_escala_edicao

    escala_exclusao = next(
        (
            e for e in escalas
            if e[0] == id_exclusao
        ),
        None
    )

    if escala_exclusao:

        nome_usuario = escala_exclusao[2]

        st.markdown("---")

        st.warning(
            f"Tem certeza que deseja excluir a escala de **{nome_usuario}**?"
        )

        col_sim, col_nao, _ = st.columns(
            [1, 1, 4]
        )

        with col_sim:

            if st.button(
                "Sim, excluir",
                type="primary",
                use_container_width=True
            ):

                try:

                    excluido = excluir_escala(
                        id_exclusao
                    )

                    if excluido:
                        st.success(
                            "Escala excluída."
                        )
                    else:
                        st.warning(
                            "Escala não encontrada."
                        )

                    st.session_state.modo_escala = None
                    st.session_state.id_escala_edicao = None

                    st.rerun()

                except Exception as erro:

                    st.error(
                        f"Não foi possível excluir: {erro}"
                    )

        with col_nao:

            if st.button(
                "Cancelar",
                use_container_width=True
            ):

                st.session_state.modo_escala = None
                st.session_state.id_escala_edicao = None

                st.rerun()


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    '<div class="rodape-sobreaviso">Sobreaviso Automate &nbsp;•&nbsp; Versão 1.0.0</div>',
    unsafe_allow_html=True
)