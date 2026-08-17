from pathlib import Path

import pandas as pd
import streamlit as st

from automacao import (
    ARQUIVO_BASE_CNPJS,
    ARQUIVO_LOGIN,
    ARQUIVO_EMAILS,
    executar_automacao,
    preparar_execucoes,
    validar_arquivos_fixos,
    validar_planilha_pedidos,
)


PASTA_PROJETO = Path(__file__).resolve().parent

st.set_page_config(
    layout="wide",
)

st.title("Bot Coletas Evelog")

col_1, _ = st.columns([1, 2])

with col_1:
    arquivo_pedidos = st.file_uploader(
        "Importe a planilha",
        type=["xlsx", "xls"],
    )

    erros_fixos = validar_arquivos_fixos()

    if not ARQUIVO_LOGIN.exists():
        st.error("dados/login.xlsx não encontrado")

    if not ARQUIVO_BASE_CNPJS.exists():
        st.error("dados/base_cnpjs.xlsx não encontrado")
        
    if not ARQUIVO_EMAILS.exists():
        st.error("emails_unidades.xlsx não encontrado")

if erros_fixos:
    st.warning(
        "Corrija os arquivos da pasta dados antes de executar a automação."
    )
    with st.expander("Ver problemas encontrados"):
        for erro in erros_fixos:
            st.write(f"• {erro}")
col_3, _ = st.columns([1, 2])

with col_3:
    if arquivo_pedidos is None:
        st.info("Selecione a base de pedidos para continuar.")
        st.stop()

try:
    df_pedidos = pd.read_excel(
        arquivo_pedidos,
        dtype=str,
    ).fillna("")
except Exception as erro:
    st.error(f"Não foi possível abrir a planilha: {erro}")
    st.stop()

erros_pedidos = validar_planilha_pedidos(df_pedidos)

st.dataframe(
    df_pedidos,
    use_container_width=True,
    hide_index=True,
)

if erros_pedidos:
    st.error("A planilha importada possui problemas:")
    for erro in erros_pedidos:
        st.write(f"• {erro}")
    st.stop()

try:
    execucoes, alertas = preparar_execucoes(df_pedidos)
except Exception as erro:
    st.error(str(erro))
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric(
    "Siglas na planilha",
    df_pedidos["SIGLA DO RESTAURANTE"].nunique(),
)
col2.metric(
    "Ordens solicitadas",
    len(execucoes),
)
col3.metric(
    "Restaurantes com CNPJ",
    len({item["sigla"] for item in execucoes}),
)

if alertas:
    st.warning("Algumas linhas não serão processadas:")
    for alerta in alertas:
        st.write(f"• {alerta}")

with st.expander("Ver fila de execução"):
    st.dataframe(
        pd.DataFrame(execucoes),
        use_container_width=True,
        hide_index=True,
    )

col_3, _ = st.columns([1, 2])

with col_3:
    executar = st.button(
        "Gerar ordens",
        type="primary",
        use_container_width=True,
        disabled=(
            bool(erros_fixos)
            or len(execucoes) == 0
        ),
    )

if executar:
    logs: list[str] = []

    try:
        with st.status(
            "Iniciando automação...",
            expanded=True,
        ) as painel:

            area_log = st.empty()

            def registrar(mensagem: str) -> None:
                logs.append(mensagem)

                area_log.code(
                    "\n".join(logs[-120:]),
                    language=None,
                )

            resultado = executar_automacao(
                execucoes=execucoes,
                headless=True,
                modo_teste=False,
                continuar_em_erro=True,
                log=registrar,
            )

            painel.update(
                label="Processamento concluído",
                state="complete",
                expanded=True,
            )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total tentado",
            resultado["total"],
        )

        c2.metric(
            "Autorizadas",
            resultado["sucessos"],
        )

        c3.metric(
            "Falhas",
            resultado["falhas"],
        )

        st.markdown("#### Resultado da execução")

        st.dataframe(
            pd.DataFrame(resultado["detalhes"]),
            use_container_width=True,
            hide_index=True,
        )

        caminho_resultado = resultado.get(
            "arquivo_resultado"
        )

        if caminho_resultado:
            caminho_resultado = Path(
                caminho_resultado
            )

            st.success(
                f"Planilha salva em "
                f"resultados/{caminho_resultado.name}"
            )

        caminho_erros = resultado.get(
            "arquivo_erros"
        )

        if caminho_erros:
            caminho_erros = Path(
                caminho_erros
            )

            st.warning(
                f"Planilha de erros salva em "
                f"resultados/{caminho_erros.name}"
            )

    except Exception as erro:
        st.error("A automação foi interrompida.")
        st.exception(erro)
