"""
Script auxiliar para geração e atualização da base de CNPJs.

Não faz parte da execução do sistema principal.
Uso manual somente quando for necessário atualizar a base.
"""

import re
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


URL_INICIAL = (
    "https://www.jadlog.com.br/"
    "FractionWeb/pages/static/home.jad"
)

ARQUIVO_ENTRADA = Path("pedidos.xlsx")
ARQUIVO_SAIDA = Path("base_cnpjs.xlsx")
PASTA_PERFIL = Path("perfil_jadlog")


def limpar_cte(valor) -> str:
    """
    Converte o CTE para texto e remove uma possível
    terminação '.0' adicionada pelo Excel.
    """
    if pd.isna(valor):
        return ""

    cte = str(valor).strip()

    if cte.endswith(".0"):
        cte = cte[:-2]

    return cte


def extrair_cnpj_do_texto(texto: str) -> str:
    """
    Extrai o CNPJ depois do campo 'CNPJ:'.

    Aceita o CNPJ formatado ou somente com números.
    Retorna somente os 14 dígitos.
    """
    if not texto:
        return ""

    resultado = re.search(
        r"CNPJ\s*:\s*"
        r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
        texto,
        flags=re.IGNORECASE,
    )

    if not resultado:
        return ""

    return re.sub(
        r"\D",
        "",
        resultado.group(1),
    )


def extrair_nome_do_texto(texto: str) -> str:
    """
    Extrai o conteúdo localizado depois do campo 'Nome:'.
    """
    if not texto:
        return ""

    resultado = re.search(
        r"Nome\s*:\s*([^\r\n]+)",
        texto,
        flags=re.IGNORECASE,
    )

    if not resultado:
        return ""

    return resultado.group(1).strip()


def validar_planilha(df: pd.DataFrame) -> None:
    """
    Confere se a planilha de entrada possui
    as colunas obrigatórias Sigla e CTE.
    """
    colunas_obrigatorias = {"Sigla", "CTE"}
    colunas_existentes = set(df.columns)

    colunas_faltando = colunas_obrigatorias - colunas_existentes

    if colunas_faltando:
        nomes = ", ".join(sorted(colunas_faltando))

        raise ValueError(
            "A planilha não possui as colunas obrigatórias: "
            f"{nomes}"
        )


def abrir_tela_pesquisa(page) -> None:
    """
    Abre o caminho Consultas > Pesquisar.
    """
    page.get_by_role(
        "link",
        name="Consultas",
    ).click()

    page.get_by_role(
        "link",
        name="Pesquisar",
    ).click()

    page.locator(
        '[id="frmPesquisa:cte"]'
    ).wait_for(
        state="visible",
        timeout=30_000,
    )


def pesquisar_remetente(page, cte: str) -> tuple[str, str]:
    """
    Pesquisa um CTE e retorna os dados do remetente:

    - CNPJ do remetente
    - Nome do remetente
    """
    abrir_tela_pesquisa(page)

    campo_cte = page.locator(
        '[id="frmPesquisa:cte"]'
    )

    campo_cte.fill("")
    campo_cte.fill(cte)

    page.get_by_role(
        "button",
        name="Processar",
    ).click()

    # Painel do remetente.
    painel_remetente = page.locator(
        '[id="j_idt289:j_idt313_content"]'
    )

    painel_remetente.wait_for(
        state="visible",
        timeout=30_000,
    )

    # Aguarda o nome aparecer no painel do remetente.
    painel_remetente.get_by_text(
        "Nome:",
        exact=False,
    ).wait_for(
        state="visible",
        timeout=30_000,
    )

    # Aguarda o CNPJ aparecer no mesmo painel.
    painel_remetente.get_by_text(
        "CNPJ:",
        exact=False,
    ).wait_for(
        state="visible",
        timeout=30_000,
    )

    # Pequena espera para garantir que todo o painel terminou de carregar.
    page.wait_for_timeout(500)

    texto_remetente = painel_remetente.inner_text()

    print("Texto do remetente:")
    print(texto_remetente)

    cnpj = extrair_cnpj_do_texto(texto_remetente)
    nome_cliente = extrair_nome_do_texto(texto_remetente)

    return cnpj, nome_cliente


def montar_base_final(df: pd.DataFrame) -> pd.DataFrame:
    """
    Monta a base que será salva.

    A coluna CTE é usada somente para as consultas
    e não aparece na planilha final.
    """
    return df[
        [
            "Sigla",
            "CNPJ",
            "Nome do Cliente",
        ]
    ].copy()


def salvar_resultados(df: pd.DataFrame) -> None:
    """
    Salva somente as colunas finais:

    - Sigla
    - CNPJ
    - Nome do Cliente
    """
    base_final = montar_base_final(df)

    base_final.to_excel(
        ARQUIVO_SAIDA,
        index=False,
    )


def recuperar_resultados_anteriores(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Caso a base de saída já exista, recupera os dados
    já encontrados pela posição das linhas.

    O CTE continua vindo exclusivamente da planilha
    de entrada.
    """
    if not ARQUIVO_SAIDA.exists():
        return df

    try:
        resultado_anterior = pd.read_excel(
            ARQUIVO_SAIDA,
            dtype=str,
        )

        resultado_anterior.columns = (
            resultado_anterior.columns
            .astype(str)
            .str.strip()
        )

        colunas_necessarias = {
            "Sigla",
            "CNPJ",
            "Nome do Cliente",
        }

        if not colunas_necessarias.issubset(
            resultado_anterior.columns
        ):
            return df

        quantidade = min(
            len(df),
            len(resultado_anterior),
        )

        for indice in range(quantidade):
            cnpj = resultado_anterior.at[
                indice,
                "CNPJ",
            ]

            nome = resultado_anterior.at[
                indice,
                "Nome do Cliente",
            ]

            if not pd.isna(cnpj):
                df.at[indice, "CNPJ"] = str(cnpj).strip()

            if not pd.isna(nome):
                df.at[
                    indice,
                    "Nome do Cliente",
                ] = str(nome).strip()

        print(
            "Resultados anteriores recuperados de "
            f"'{ARQUIVO_SAIDA.name}'."
        )

    except Exception as erro:
        print(
            "Não foi possível recuperar a base anterior."
        )
        print(f"Detalhes: {erro}")

    return df


def executar() -> None:
    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(
            f"O arquivo '{ARQUIVO_ENTRADA}' não foi encontrado."
        )

    df = pd.read_excel(
        ARQUIVO_ENTRADA,
        dtype={
            "Sigla": str,
            "CTE": str,
        },
    )

    # Limpa possíveis espaços nos nomes das colunas.
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    validar_planilha(df)

    df["Sigla"] = (
        df["Sigla"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["CTE"] = df["CTE"].apply(limpar_cte)

    # Cria as colunas de resultado.
    df["CNPJ"] = ""
    df["Nome do Cliente"] = ""

    # Recupera o que já tiver sido salvo em uma execução anterior.
    df = recuperar_resultados_anteriores(df)

    PASTA_PERFIL.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PASTA_PERFIL),
            headless=False,
            slow_mo=200,
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()

        print("Abrindo o sistema da Jadlog...")

        page.goto(
            URL_INICIAL,
            wait_until="domcontentloaded",
            timeout=120_000,
        )

        print()
        print(
            "Faça o login no navegador, caso seja necessário."
        )

        input(
            "Depois de entrar no sistema, pressione ENTER aqui..."
        )

        total = len(df)

        # Evita consultar novamente um mesmo CTE durante
        # a mesma execução.
        cache_por_cte: dict[str, tuple[str, str]] = {}

        for indice, linha in df.iterrows():
            sigla = str(linha["Sigla"]).strip()
            cte = str(linha["CTE"]).strip()

            cnpj_existente = str(
                df.at[indice, "CNPJ"]
            ).strip()

            nome_existente = str(
                df.at[indice, "Nome do Cliente"]
            ).strip()

            print()
            print("=" * 60)
            print(f"[{indice + 1}/{total}]")
            print(f"Sigla: {sigla}")
            print(f"CTE: {cte}")

            if not cte:
                print("CTE vazio. Linha ignorada.")

                df.at[indice, "CNPJ"] = "CTE VAZIO"
                df.at[indice, "Nome do Cliente"] = ""

                salvar_resultados(df)
                continue

            # Ignora somente registros que já possuem CNPJ e nome.
            # Para refazer todas as consultas, apague o arquivo
            # base_cnpjs.xlsx antes de executar.
            if (
                re.fullmatch(r"\d{14}", cnpj_existente)
                and nome_existente
                and nome_existente not in {
                    "NÃO ENCONTRADO",
                    "ERRO: TIMEOUT",
                    "ERRO NA PESQUISA",
                }
            ):
                print("Linha já preenchida. Consulta ignorada.")
                print(f"CNPJ: {cnpj_existente}")
                print(f"Nome: {nome_existente}")

                cache_por_cte[cte] = (
                    cnpj_existente,
                    nome_existente,
                )

                continue

            if cte in cache_por_cte:
                cnpj, nome_cliente = cache_por_cte[cte]

                df.at[indice, "CNPJ"] = cnpj
                df.at[
                    indice,
                    "Nome do Cliente",
                ] = nome_cliente

                print("CTE já consultado nesta execução.")
                print(f"CNPJ: {cnpj}")
                print(f"Nome: {nome_cliente}")

                salvar_resultados(df)
                continue

            try:
                cnpj, nome_cliente = pesquisar_remetente(
                    page=page,
                    cte=cte,
                )

                if cnpj:
                    df.at[indice, "CNPJ"] = cnpj
                else:
                    df.at[
                        indice,
                        "CNPJ",
                    ] = "NÃO ENCONTRADO"

                if nome_cliente:
                    df.at[
                        indice,
                        "Nome do Cliente",
                    ] = nome_cliente
                else:
                    df.at[
                        indice,
                        "Nome do Cliente",
                    ] = "NÃO ENCONTRADO"

                cache_por_cte[cte] = (
                    df.at[indice, "CNPJ"],
                    df.at[
                        indice,
                        "Nome do Cliente",
                    ],
                )

                print("Consulta concluída.")
                print(
                    f"CNPJ: {df.at[indice, 'CNPJ']}"
                )
                print(
                    "Nome: "
                    f"{df.at[indice, 'Nome do Cliente']}"
                )

            except PlaywrightTimeoutError as erro:
                print(
                    "Tempo limite excedido nessa pesquisa."
                )
                print(f"Detalhes: {erro}")

                df.at[
                    indice,
                    "CNPJ",
                ] = "ERRO: TIMEOUT"

                df.at[
                    indice,
                    "Nome do Cliente",
                ] = "ERRO: TIMEOUT"

                try:
                    page.goto(
                        URL_INICIAL,
                        wait_until="domcontentloaded",
                        timeout=120_000,
                    )
                except Exception:
                    pass

            except Exception as erro:
                print("Erro durante a pesquisa.")
                print(f"Detalhes: {erro}")

                df.at[
                    indice,
                    "CNPJ",
                ] = "ERRO NA PESQUISA"

                df.at[
                    indice,
                    "Nome do Cliente",
                ] = "ERRO NA PESQUISA"

                try:
                    page.goto(
                        URL_INICIAL,
                        wait_until="domcontentloaded",
                        timeout=120_000,
                    )
                except Exception:
                    pass

            # Salva depois de cada consulta para não perder
            # o andamento em caso de interrupção.
            salvar_resultados(df)

            time.sleep(1)

        context.close()

    salvar_resultados(df)

    print()
    print("=" * 60)
    print("Processo finalizado.")
    print(
        f"Base salva em: {ARQUIVO_SAIDA.resolve()}"
    )


if __name__ == "__main__":
    executar()