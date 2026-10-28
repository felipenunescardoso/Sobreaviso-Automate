import streamlit as st
from datetime import datetime, date, time

from cadastros import (
    listar_escalas
)

from executor import (
    buscar_escala_permitida,
    registrar_acionamento,
    alterar_acionamento,
    excluir_acionamento,
    encerrar_escala_sistema,
    listar_lancamentos_escala_permitidos,
    listar_usuarios_permitidos_acionamentos,
    formatar_minutos
)


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

st.set_page_config(
    page_title="Preenchimento de Sobreaviso",
    page_icon="🕒",
    layout="wide"
)


st.markdown("""
<style>

/* ============================================================
   FONTE PADRÃO DA APLICAÇÃO
   ============================================================ */
html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}

/* ============================================================
   FUNDO GERAL DA APLICAÇÃO
   ============================================================ */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(88, 101, 242, 0.05), transparent 22%),
        #F7F9FC;
    color: #111827;
}

/* ============================================================
   ÁREA PRINCIPAL / MARGENS DA PÁGINA
   ============================================================ */
.block-container {
    padding-top: 2.2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 4rem;
    max-width: 1600px;
}

/* ============================================================
   TÍTULO PRINCIPAL
   ============================================================ */
.titulo-pagina {
    font-size: 38px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: -0.8px;
    color: #111827;
    margin-bottom: 10px;
}

/* ============================================================
   SUBTÍTULO DA PÁGINA
   ============================================================ */
.subtitulo-pagina {
    font-size: 16px;
    line-height: 1.5;
    color: #697386;
    margin-bottom: 28px;
}

/* ============================================================
   TÍTULOS DAS SEÇÕES
   ============================================================ */
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

/* ============================================================
   LINHAS SEPARADORAS
   ============================================================ */
hr {
    border: none !important;
    border-top: 1px solid #E5E7EB !important;
    margin-top: 28px !important;
    margin-bottom: 28px !important;
}

/* ============================================================
   BOTÕES - ESTADO NORMAL
   ============================================================ */
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

/* Garante texto e ícones brancos dentro dos botões */
div.stButton > button *,
div.stFormSubmitButton > button * {
    color: white !important;
}

/* ============================================================
   BOTÕES - PASSAR O MOUSE
   ============================================================ */
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

/* ============================================================
   CARDS DOS LANÇAMENTOS - ACIONAMENTO / SOBREAVISO
   ============================================================ */
div[class*="st-key-acionamento_card_"],
div[class*="st-key-sobreaviso_card_"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08) !important;
    padding: 20px 22px !important;
    margin-top: 8px !important;
    margin-bottom: 14px !important;
}

/* ============================================================
   CAMPOS DE DATA
   ============================================================ */
div[data-testid="stDateInput"] input {
    background-color: #262730 !important;
    color: white !important;
    border-radius: 9px !important;
}

div[data-testid="stDateInput"] > div > div {
    background-color: #262730 !important;
}

/* Ícone do calendário */
div[data-testid="stDateInput"] svg {
    fill: white !important;
    color: white !important;
}

/* ============================================================
   CAMPO MOTIVO / TEXTAREA
   ============================================================ */
/* Texto digitado pelo usuário */
div[data-testid="stTextArea"] textarea {
    background-color: #262730 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}

/* Mantém o fundo do componente consistente em qualquer tema do navegador */
div[data-testid="stTextArea"] > div > div {
    background-color: #262730 !important;
}

/* Texto de exemplo antes da digitação */
div[data-testid="stTextArea"] textarea::placeholder {
    color: #98A2B3 !important;
    -webkit-text-fill-color: #98A2B3 !important;
    opacity: 1 !important;
}

/* ============================================================
   LABELS DOS CAMPOS
   ============================================================ */
label {
    color: #344054 !important;
    font-weight: 600 !important;
}

/* ============================================================
   MENSAGENS NEUTRAS
   Substitui avisos amarelos por blocos brancos com texto escuro
   ============================================================ */
.mensagem-neutra {
    background: #FFFFFF;
    color: #111827 !important;
    border: 1px solid #E2E7EF;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 14px;
    font-weight: 500;
    margin-top: 8px;
    margin-bottom: 8px;
}

/* ============================================================
   TEMPO DOS LANÇAMENTOS
   Acionamento e sobreaviso usam apresentação neutra
   ============================================================ */
.tempo-lancamento {
    background: #F3F4F6;
    color: #111827 !important;
    border: 1px solid #E2E7EF;
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
    font-weight: 700;
    font-size: 14px;
}

/* ============================================================
   ELEMENTOS NATIVOS DO STREAMLIT OCULTOS
   ============================================================ */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* ============================================================
   RODAPÉ DO SISTEMA
   ============================================================ */
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
    '<div class="titulo-pagina">Preenchimento de Sobreaviso</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-pagina">'
    'Registre os acionamentos da sua escala. As linhas de sobreaviso são calculadas automaticamente pelo sistema.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SESSÃO / USUÁRIO LOGADO
# ============================================================

if (
    "usuario" not in st.session_state
    or not st.session_state["usuario"]
):
    st.error(
        "Sessão não encontrada. Faça o login novamente."
    )
    st.stop()


usuario_logado = st.session_state["usuario"]

id_usuario_executor = usuario_logado["id_usuario"]
nome_usuario_logado = usuario_logado["nome"]
perfil_executor = str(
    usuario_logado["perfil"]
).upper()


# ============================================================
# ESTADO
# ============================================================

if "modo_acionamento" not in st.session_state:
    st.session_state.modo_acionamento = None

if "id_lancamento_edicao" not in st.session_state:
    st.session_state.id_lancamento_edicao = None

if "mostrar_encerramento" not in st.session_state:
    st.session_state.mostrar_encerramento = False


# ============================================================
# USUÁRIO
# ============================================================

try:
    usuarios_permitidos = listar_usuarios_permitidos_acionamentos(
        id_usuario_executor
    )

except Exception as erro:
    st.error(
        f"Erro ao carregar usuários permitidos: {erro}"
    )
    usuarios_permitidos = []


if not usuarios_permitidos:

    st.markdown(
        '<div class="mensagem-neutra">'
        'Nenhum usuário disponível para preenchimento.'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()


# ============================================================
# TÉCNICO: NÃO ESCOLHE USUÁRIO
# ADMIN/GESTOR: COMBO SOMENTE COM USUÁRIOS PERMITIDOS
# ============================================================

if perfil_executor == "TECNICO":

    id_usuario = id_usuario_executor

    st.info(
        f"**Usuário:** {nome_usuario_logado}"
    )

else:

    mapa_usuarios = {
        id_usuario: nome
        for id_usuario, nome
        in usuarios_permitidos
    }

    id_usuario = st.selectbox(
        "Usuário",
        options=list(
            mapa_usuarios.keys()
        ),
        format_func=lambda x: mapa_usuarios[x],
        key="preenchimento_usuario"
    )


# ============================================================
# ESCALAS DO USUÁRIO
# ============================================================

try:
    escalas_usuario = listar_escalas(
        id_usuario=id_usuario
    )
except Exception as erro:
    st.error(f"Erro ao carregar escalas: {erro}")
    escalas_usuario = []


if not escalas_usuario:

    st.markdown(
        '<div class="mensagem-neutra">Este usuário não possui escalas cadastradas.</div>',
        unsafe_allow_html=True
    )
    st.stop()


mapa_escalas = {
    e[0]: (
        f"{e[3].strftime('%d/%m/%Y %H:%M')} "
        f"até {e[4].strftime('%d/%m/%Y %H:%M')}"
    )
    for e in escalas_usuario
}


id_escala = st.selectbox(
    "Escala",
    options=list(mapa_escalas.keys()),
    format_func=lambda x: mapa_escalas[x],
    key="preenchimento_escala"
)


# ============================================================
# DADOS DA ESCALA
# ============================================================

try:
    escala = buscar_escala_permitida(
        id_usuario_executor=id_usuario_executor,
        id_usuario=id_usuario,
        id_escala=id_escala
    )
except Exception as erro:
    st.error(f"Erro ao consultar escala: {erro}")
    st.stop()


if not escala:

    st.error(
        "A escala selecionada não pertence ao usuário informado."
    )
    st.stop()


(
    _,
    _,
    escala_inicio,
    escala_fim,
    ordem,
    replicacao,
    encerrada,
    data_hora_encerramento,
    id_cidade,
    uf
) = escala


col1, col2, col3, col4 = st.columns(
    [2.3, 2.3, 1, 1.4]
)

with col1:
    st.info(
        f"**Início previsto**\n\n"
        f"{escala_inicio.strftime('%d/%m/%Y %H:%M')}"
    )

with col2:
    st.info(
        f"**Fim previsto**\n\n"
        f"{escala_fim.strftime('%d/%m/%Y %H:%M')}"
    )

with col3:
    st.info(
        f"**Ordem**\n\n{ordem}"
    )

with col4:

    if encerrada:
        st.success("● Escala encerrada")
    else:
        st.markdown(
            '<div class="mensagem-neutra">● Escala aberta</div>',
            unsafe_allow_html=True
        )


if encerrada and data_hora_encerramento:
    st.caption(
        f"Encerrada em: "
        f"{data_hora_encerramento.strftime('%d/%m/%Y %H:%M')}"
    )


# ============================================================
# AÇÕES
# ============================================================

st.markdown("---")

col_novo, col_encerrar, _ = st.columns(
    [1.2, 1.2, 4]
)

with col_novo:

    if st.button(
        "➕ Novo Acionamento",
        use_container_width=True,
        disabled=encerrada
    ):
        st.session_state.modo_acionamento = "novo"
        st.session_state.id_lancamento_edicao = None
        st.session_state.mostrar_encerramento = False


with col_encerrar:

    if st.button(
        "✅ Encerrar Escala",
        use_container_width=True,
        disabled=encerrada
    ):
        st.session_state.mostrar_encerramento = True
        st.session_state.modo_acionamento = None
        st.session_state.id_lancamento_edicao = None


# ============================================================
# NOVO ACIONAMENTO
# ============================================================

if (
    st.session_state.modo_acionamento == "novo"
    and not encerrada
):

    st.markdown("### Novo Acionamento")

    with st.container(
        border=True,
        key="novo_acionamento_card"
    ):

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data Início",
                value=date.today(),
                format="DD/MM/YYYY",
                key="novo_acionamento_data_inicio"
            )

        with col2:
            hora_inicio = st.time_input(
                "Hora Início",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0
                ),
                key="novo_acionamento_hora_inicio"
            )

        col3, col4 = st.columns(2)

        with col3:
            data_fim = st.date_input(
                "Data Fim",
                value=date.today(),
                format="DD/MM/YYYY",
                key="novo_acionamento_data_fim"
            )

        with col4:
            hora_fim = st.time_input(
                "Hora Fim",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0
                ),
                key="novo_acionamento_hora_fim"
            )

        motivo = st.text_area(
            "Motivo",
            placeholder="Informe o motivo do acionamento...",
            key="novo_acionamento_motivo"
        )

        col_salvar, col_cancelar = st.columns(2)

        with col_salvar:
            salvar = st.button(
                "Salvar Acionamento",
                key="salvar_acionamento",
                use_container_width=True
            )

        with col_cancelar:
            cancelar = st.button(
                "Cancelar",
                key="cancelar_acionamento",
                use_container_width=True
            )

        if salvar:

            inicio = datetime.combine(
                data_inicio,
                hora_inicio
            )

            fim = datetime.combine(
                data_fim,
                hora_fim
            )

            try:

                id_lancamento = registrar_acionamento(
                    id_usuario=id_usuario,
                    id_usuario_executor=id_usuario_executor,
                    id_escala=id_escala,
                    data_hora_inicio=inicio,
                    data_hora_fim=fim,
                    motivo=motivo
                )

                st.success(
                    f"Acionamento registrado com sucesso. "
                    f"ID: {id_lancamento}"
                )

                st.session_state.modo_acionamento = None
                st.rerun()

            except Exception as erro:
                st.error(str(erro))

        if cancelar:
            st.session_state.modo_acionamento = None
            st.rerun()


# ============================================================
# ENCERRAMENTO
# ============================================================

if (
    st.session_state.mostrar_encerramento
    and not encerrada
):

    st.markdown("### Encerrar Escala")

    with st.container(
        border=True,
        key="encerrar_escala_card"
    ):

        usar_agora = st.checkbox(
            "Usar data e hora atual",
            value=True,
            key="encerrar_usar_agora"
        )

        if usar_agora:

            agora = datetime.now().replace(
                second=0,
                microsecond=0
            )

            # O front apenas reflete a regra do backend:
            # antes/igual ao fim previsto -> usa o momento atual;
            # depois do fim previsto -> limita ao fim previsto.
            encerramento = min(
                agora,
                escala_fim
            )

            st.info(
                f"Encerramento considerado: "
                f"{encerramento.strftime('%d/%m/%Y %H:%M')}"
            )

        else:

            col1, col2 = st.columns(2)

            with col1:
                data_encerramento = st.date_input(
                    "Data do Encerramento",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    key="data_encerramento"
                )

            with col2:
                hora_encerramento = st.time_input(
                    "Hora do Encerramento",
                    value=datetime.now().time().replace(
                        second=0,
                        microsecond=0
                    ),
                    key="hora_encerramento"
                )

            encerramento_informado = datetime.combine(
                data_encerramento,
                hora_encerramento
            )

            encerramento = min(
                encerramento_informado,
                escala_fim
            )

            st.info(
                f"Encerramento considerado: "
                f"{encerramento.strftime('%d/%m/%Y %H:%M')}"
            )

        col_sim, col_nao = st.columns(2)

        with col_sim:

            confirmar = st.button(
                "Confirmar Encerramento",
                key="confirmar_encerramento",
                use_container_width=True
            )

        with col_nao:

            cancelar_encerramento = st.button(
                "Cancelar",
                key="cancelar_encerramento",
                use_container_width=True
            )

        if confirmar:

            try:

                resultado = encerrar_escala_sistema(
                    id_escala=id_escala,
                    data_hora_encerramento=encerramento
                )

                st.success(
                    "Escala encerrada com sucesso em "
                    f"{resultado['fim_efetivo'].strftime('%d/%m/%Y %H:%M')}."
                )

                st.session_state.mostrar_encerramento = False
                st.rerun()

            except Exception as erro:
                st.error(str(erro))

        if cancelar_encerramento:
            st.session_state.mostrar_encerramento = False
            st.rerun()


# ============================================================
# LANÇAMENTOS
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="titulo-secao">Lançamentos da Escala</div>',
    unsafe_allow_html=True
)


try:
    lancamentos = listar_lancamentos_escala_permitidos(
        id_usuario_executor=id_usuario_executor,
        id_usuario=id_usuario,
        id_escala=id_escala
    )
except Exception as erro:
    st.error(
        f"Erro ao consultar lançamentos: {erro}"
    )
    lancamentos = []


if not lancamentos:

    st.info(
        "Nenhum lançamento gerado para esta escala."
    )

else:

    for lancamento in lancamentos:

        (
            id_lancamento,
            tipo,
            inicio,
            fim,
            minutos,
            motivo,
            origem,
            id_competencia
        ) = lancamento

        chave_card = (
            f"acionamento_card_{id_lancamento}"
            if tipo == "ACIONAMENTO"
            else f"sobreaviso_card_{id_lancamento}"
        )

        with st.container(
            border=True,
            key=chave_card
        ):

            if tipo == "ACIONAMENTO":

                col_info, col_tempo, col_editar, col_excluir = st.columns(
                    [5, 1.2, 1, 1]
                )

            else:

                col_info, col_tempo = st.columns(
                    [6, 1.4]
                )

            with col_info:

                if tipo == "ACIONAMENTO":
                    st.markdown("### ⚡ Acionamento")
                else:
                    st.markdown("### 🕒 Sobreaviso")

                st.write(
                    f"**{inicio.strftime('%d/%m/%Y %H:%M')} "
                    f"→ {fim.strftime('%d/%m/%Y %H:%M')}**"
                )

                if motivo:
                    st.caption(
                        f"Motivo: {motivo}"
                    )

            with col_tempo:

                st.markdown(
                    f'<div class="tempo-lancamento">{formatar_minutos(minutos)}</div>',
                    unsafe_allow_html=True
                )

            if tipo == "ACIONAMENTO":

                with col_editar:

                    if st.button(
                        "✏️ Editar",
                        key=f"editar_acionamento_{id_lancamento}",
                        use_container_width=True,
                        disabled=encerrada
                    ):
                        st.session_state.modo_acionamento = "editar"
                        st.session_state.id_lancamento_edicao = id_lancamento
                        st.session_state.mostrar_encerramento = False

                with col_excluir:

                    if st.button(
                        "🗑️ Excluir",
                        key=f"excluir_acionamento_{id_lancamento}",
                        use_container_width=True,
                        disabled=encerrada
                    ):
                        st.session_state.modo_acionamento = "excluir"
                        st.session_state.id_lancamento_edicao = id_lancamento
                        st.session_state.mostrar_encerramento = False


# ============================================================
# EDITAR ACIONAMENTO
# ============================================================

if (
    st.session_state.modo_acionamento == "editar"
    and st.session_state.id_lancamento_edicao
    and not encerrada
):

    id_edicao = st.session_state.id_lancamento_edicao

    lancamento_edicao = next(
        (
            l for l in lancamentos
            if l[0] == id_edicao
            and l[1] == "ACIONAMENTO"
        ),
        None
    )

    if lancamento_edicao:

        inicio_atual = lancamento_edicao[2]
        fim_atual = lancamento_edicao[3]
        motivo_atual = lancamento_edicao[5] or ""

        st.markdown("---")
        st.markdown("### Editar Acionamento")

        with st.container(
            border=True,
            key=f"editar_acionamento_card_{id_edicao}"
        ):

            col1, col2 = st.columns(2)

            with col1:
                data_inicio_edit = st.date_input(
                    "Data Início",
                    value=inicio_atual.date(),
                    format="DD/MM/YYYY",
                    key=f"editar_data_inicio_{id_edicao}"
                )

            with col2:
                hora_inicio_edit = st.time_input(
                    "Hora Início",
                    value=inicio_atual.time(),
                    key=f"editar_hora_inicio_{id_edicao}"
                )

            col3, col4 = st.columns(2)

            with col3:
                data_fim_edit = st.date_input(
                    "Data Fim",
                    value=fim_atual.date(),
                    format="DD/MM/YYYY",
                    key=f"editar_data_fim_{id_edicao}"
                )

            with col4:
                hora_fim_edit = st.time_input(
                    "Hora Fim",
                    value=fim_atual.time(),
                    key=f"editar_hora_fim_{id_edicao}"
                )

            motivo_edit = st.text_area(
                "Motivo",
                value=motivo_atual,
                key=f"editar_motivo_{id_edicao}"
            )

            col_salvar, col_cancelar = st.columns(2)

            with col_salvar:
                salvar_edicao = st.button(
                    "Salvar Alterações",
                    key=f"salvar_edicao_{id_edicao}",
                    use_container_width=True
                )

            with col_cancelar:
                cancelar_edicao = st.button(
                    "Cancelar",
                    key=f"cancelar_edicao_{id_edicao}",
                    use_container_width=True
                )

            if salvar_edicao:

                novo_inicio = datetime.combine(
                    data_inicio_edit,
                    hora_inicio_edit
                )

                novo_fim = datetime.combine(
                    data_fim_edit,
                    hora_fim_edit
                )

                try:

                    alterado = alterar_acionamento(
                        id_usuario=id_usuario,
                        id_usuario_executor=id_usuario_executor,
                        id_lancamento=id_edicao,
                        data_hora_inicio=novo_inicio,
                        data_hora_fim=novo_fim,
                        motivo=motivo_edit
                    )

                    if alterado:
                        st.success(
                            "Acionamento alterado com sucesso."
                        )

                    st.session_state.modo_acionamento = None
                    st.session_state.id_lancamento_edicao = None
                    st.rerun()

                except Exception as erro:
                    st.error(str(erro))

            if cancelar_edicao:
                st.session_state.modo_acionamento = None
                st.session_state.id_lancamento_edicao = None
                st.rerun()


# ============================================================
# EXCLUIR ACIONAMENTO
# ============================================================

if (
    st.session_state.modo_acionamento == "excluir"
    and st.session_state.id_lancamento_edicao
    and not encerrada
):

    id_exclusao = st.session_state.id_lancamento_edicao

    lancamento_exclusao = next(
        (
            l for l in lancamentos
            if l[0] == id_exclusao
            and l[1] == "ACIONAMENTO"
        ),
        None
    )

    if lancamento_exclusao:

        st.markdown("---")

        st.markdown(
            '<div class="mensagem-neutra">'
            'Tem certeza que deseja excluir o acionamento de '
            f'{lancamento_exclusao[2].strftime("%d/%m/%Y %H:%M")} '
            f'até {lancamento_exclusao[3].strftime("%H:%M")}?'
            '</div>',
            unsafe_allow_html=True
        )

        col_sim, col_nao, _ = st.columns(
            [1, 1, 4]
        )

        with col_sim:

            if st.button(
                "Sim, excluir",
                key=f"confirmar_exclusao_{id_exclusao}",
                use_container_width=True
            ):

                try:

                    excluido = excluir_acionamento(
                        id_usuario=id_usuario,
                        id_usuario_executor=id_usuario_executor,
                        id_lancamento=id_exclusao
                    )

                    if excluido:
                        st.success(
                            "Acionamento excluído com sucesso."
                        )

                    st.session_state.modo_acionamento = None
                    st.session_state.id_lancamento_edicao = None
                    st.rerun()

                except Exception as erro:
                    st.error(str(erro))

        with col_nao:

            if st.button(
                "Cancelar",
                key=f"cancelar_exclusao_{id_exclusao}",
                use_container_width=True
            ):
                st.session_state.modo_acionamento = None
                st.session_state.id_lancamento_edicao = None
                st.rerun()


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    '<div class="rodape-sobreaviso">'
    'Sobreaviso Automate &nbsp;•&nbsp; Versão 1.0.0'
    '</div>',
    unsafe_allow_html=True
)