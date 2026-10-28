import streamlit as st
from datetime import date

from extrator_pdf import (
    listar_usuarios_permitidos_extracao,
    listar_competencias_extracao,
    montar_data_referencia_competencia,
    calcular_competencia,
    consultar_extracao_permitida,
    gerar_pdf_permitido
)

from extrator_excel import (
    gerar_excel_permitido
)


st.set_page_config(
    page_title="Automate - Sobreaviso",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

st.markdown("""
<style>

/* Fundo geral */
.stApp {
    background:
        radial-gradient(
            circle at top left,
            rgba(88, 101, 242, 0.05),
            transparent 22%
        ),
        #F7F9FC !important;

    color: #111827 !important;
}

/* Área principal */
.block-container {
    padding-top: 2.2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 4rem;
    max-width: 1600px;
}

/* Títulos e textos fora dos componentes */
h1,
h2,
h3,
h4,
h5,
h6,
p {
    color: #111827 !important;
}

/* Labels */
label,
[data-testid="stWidgetLabel"] p {
    color: #344054 !important;
    font-weight: 600 !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background-color: #262730 !important;
    color: #FFFFFF !important;
    border-radius: 9px !important;
}

div[data-baseweb="select"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div[data-baseweb="select"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}

/* Number input */
div[data-testid="stNumberInput"] input {
    background-color: #262730 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}

div[data-testid="stNumberInput"] button {
    background-color: #262730 !important;
    color: #FFFFFF !important;
}

div[data-testid="stNumberInput"] button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Botões */
div.stButton > button,
div.stDownloadButton > button {
    border-radius: 10px !important;
    min-height: 44px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    border: 1px solid #151A24 !important;
    background:
        linear-gradient(
            180deg,
            #171C27 0%,
            #10141D 100%
        ) !important;
    color: #FFFFFF !important;
    box-shadow:
        0 2px 5px
        rgba(16, 24, 40, 0.14) !important;
}

div.stButton > button *,
div.stDownloadButton > button * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    border-color: #635BFF !important;
    transform: translateY(-1px);
    box-shadow:
        0 5px 14px
        rgba(16, 24, 40, 0.18) !important;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E7EF !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Alertas */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* Downloads */
div[data-testid="stDownloadButton"] button {
    width: 100% !important;
}

/* Elementos nativos */
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
# TÍTULO
# ============================================================

st.title("Automate - Sobreaviso")
st.subheader("Extrator de Sobreaviso")


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
# CARGAS
# ============================================================

try:

    usuarios = listar_usuarios_permitidos_extracao(
        id_usuario_executor
    )

except Exception as erro:

    st.error(
        f"Erro ao carregar usuários permitidos: {erro}"
    )

    usuarios = []


if not usuarios:

    st.warning(
        "Nenhum usuário disponível para extração."
    )

    st.stop()


competencias = listar_competencias_extracao()


# ============================================================
# USUÁRIO
# ============================================================

if perfil_executor == "TECNICO":

    id_usuario = id_usuario_executor

    st.info(
        f"**Usuário:** {nome_usuario_logado}"
    )

else:

    usuarios_dict = {
        nome: id_usuario
        for id_usuario, nome in usuarios
    }

    nome_usuario = st.selectbox(
        "Técnico",
        options=list(
            usuarios_dict.keys()
        )
    )

    id_usuario = usuarios_dict[
        nome_usuario
    ]


# ============================================================
# COMPETÊNCIA
# ============================================================

st.markdown(
    "### Competência"
)

col1, col2 = st.columns(2)


with col1:

    nomes_competencias = list(
        competencias.keys()
    )

    indice_padrao = (
        date.today().month - 1
    )

    nome_competencia = st.selectbox(
        "Competência",
        options=nomes_competencias,
        index=indice_padrao
    )

    mes_fim = competencias[
        nome_competencia
    ]


with col2:

    ano = st.number_input(
        "Ano",
        min_value=2025,
        max_value=2100,
        value=date.today().year,
        step=1
    )


# ============================================================
# PERÍODO
# ============================================================

data_referencia = montar_data_referencia_competencia(
    ano=ano,
    mes_fim=mes_fim
)

inicio, fim = calcular_competencia(
    data_referencia
)

st.info(
    f"Competência: {nome_competencia} | "
    f"Período: {inicio:%d/%m/%Y} "
    f"até {fim:%d/%m/%Y}"
)


# ============================================================
# CONSULTAR + GERAR PDF + EXCEL
# ============================================================

if st.button(
    "Consultar lançamentos",
    type="primary"
):

    st.session_state.pop(
        "extracao_pdf_bytes",
        None
    )

    st.session_state.pop(
        "extracao_pdf_nome",
        None
    )

    st.session_state.pop(
        "extracao_excel_bytes",
        None
    )

    st.session_state.pop(
        "extracao_excel_nome",
        None
    )

    try:

        resultado = consultar_extracao_permitida(
            id_usuario_executor=id_usuario_executor,
            id_usuario_alvo=id_usuario,
            ano=ano,
            mes_fim=mes_fim
        )

        st.session_state[
            "extracao_registros"
        ] = resultado[
            "registros"
        ]

        st.session_state[
            "extracao_id_usuario"
        ] = id_usuario

        st.session_state[
            "extracao_data_referencia"
        ] = resultado[
            "data_referencia"
        ]

        st.session_state[
            "extracao_competencia_nome"
        ] = nome_competencia

        # ====================================================
        # GERA PDF
        # ====================================================

        arquivo_pdf = gerar_pdf_permitido(
            id_usuario_executor=id_usuario_executor,
            id_usuario_alvo=id_usuario,
            data_referencia=resultado[
                "data_referencia"
            ]
        )

        with open(
            arquivo_pdf,
            "rb"
        ) as pdf:

            st.session_state[
                "extracao_pdf_bytes"
            ] = pdf.read()

        st.session_state[
            "extracao_pdf_nome"
        ] = arquivo_pdf.name

        # ====================================================
        # GERA EXCEL
        # ====================================================

        arquivo_excel = gerar_excel_permitido(
            id_usuario_executor=id_usuario_executor,
            id_usuario_alvo=id_usuario,
            data_referencia=resultado[
                "data_referencia"
            ]
        )

        with open(
            arquivo_excel,
            "rb"
        ) as excel:

            st.session_state[
                "extracao_excel_bytes"
            ] = excel.read()

        st.session_state[
            "extracao_excel_nome"
        ] = arquivo_excel.name

    except Exception as erro:

        st.error(
            f"Erro ao consultar/gerar arquivos: {erro}"
        )


# ============================================================
# RESULTADO
# ============================================================

if "extracao_registros" in st.session_state:

    registros = st.session_state[
        "extracao_registros"
    ]

    st.markdown(
        "### Lançamentos encontrados"
    )

    if registros:

        dados_tabela = []

        for registro in registros:

            dados_tabela.append(
                {
                    "Escala": registro[
                        "id_escala"
                    ],

                    "Tipo": registro[
                        "tipo"
                    ],

                    "Data": registro[
                        "data_hora_inicio"
                    ].strftime(
                        "%d/%m/%Y"
                    ),

                    "Início": registro[
                        "data_hora_inicio"
                    ].strftime(
                        "%H:%M"
                    ),

                    "Fim": registro[
                        "data_hora_fim"
                    ].strftime(
                        "%H:%M"
                    ),

                    "Motivo": (
                        registro[
                            "motivo"
                        ]
                        or ""
                    )
                }
            )

        st.dataframe(
            dados_tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Escala": st.column_config.NumberColumn(
                    "Escala",
                    format="%d"
                ),
                "Tipo": st.column_config.TextColumn(
                    "Tipo"
                ),
                "Data": st.column_config.TextColumn(
                    "Data"
                ),
                "Início": st.column_config.TextColumn(
                    "Início"
                ),
                "Fim": st.column_config.TextColumn(
                    "Fim"
                ),
                "Motivo": st.column_config.TextColumn(
                    "Motivo",
                    width="large"
                )
            }
        )

        st.write(
            f"**Total de linhas:** "
            f"{len(registros)}"
        )

    else:

        st.warning(
            "Nenhum lançamento encontrado "
            "para essa competência."
        )

    # ========================================================
    # DOWNLOADS
    # ========================================================

    col_pdf, col_excel = st.columns(2)

    with col_pdf:

        if (
            "extracao_pdf_bytes"
            in st.session_state
            and
            "extracao_pdf_nome"
            in st.session_state
        ):

            st.download_button(
                label="Baixar PDF",
                data=st.session_state[
                    "extracao_pdf_bytes"
                ],
                file_name=st.session_state[
                    "extracao_pdf_nome"
                ],
                mime="application/pdf",
                use_container_width=True
            )

    with col_excel:

        if (
            "extracao_excel_bytes"
            in st.session_state
            and
            "extracao_excel_nome"
            in st.session_state
        ):

            st.download_button(
                label="Baixar Excel",
                data=st.session_state[
                    "extracao_excel_bytes"
                ],
                file_name=st.session_state[
                    "extracao_excel_nome"
                ],
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True
            )