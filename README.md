# Bot Coletas Jadlog

Aplicativo Streamlit local para gerar solicitações de coleta no Jadlog.

## 1. Estrutura

```text
BotColetas_Jadlog_Final/
├── app.py
├── automacao.py
├── requirements.txt
├── dados/
│   ├── login.xlsx
│   └── base_cnpjs.xlsx
├── resultados/
├── iniciar_windows.bat
└── iniciar_linux.sh
```

As pastas `dados` e `resultados` vêm vazias.

## 2. Arquivo dados/login.xlsx

Crie uma planilha com exatamente estas colunas:

| USER | PASSWORD |
|---|---|
| seu_usuario | sua_senha |

A primeira linha de dados será utilizada no login.

## 3. Arquivo dados/base_cnpjs.xlsx

Crie uma planilha com exatamente estas colunas:

| SIGLA | CNPJ | NOME DO CLIENTE |
|---|---|---|
| SIGLA1 | 00000000000000 | Nome do cliente |

O CNPJ do remetente é localizado pela sigla.

O CNPJ do destinatário é fixo:

```text
42591651000143
```

## 4. Planilha importada no app

A planilha enviada pelo usuário deve possuir:

| SIGLA DO RESTAURANTE | NUMERO DE ORDENS |
|---|---:|
| SIGLA1 | 3 |
| SIGLA2 | 1 |

No exemplo, serão realizadas quatro execuções.

## 5. Loop da automação

O login é realizado uma vez.

Para cada ordem, o caminho completo recomeça em:

```python
page.get_by_role("link", name="Operacional")
```

Depois segue:

1. Operacional
2. Ordem de coleta
3. Solicitação de Coleta
4. Preenchimento dos campos
5. Colagem do CNPJ do remetente
6. Colagem do CNPJ do destinatário
7. Seleção da modalidade CORPORATE por último
8. Gerar Coleta
9. Captura do número exibido na mensagem

## 6. Resultado

Ao final, o app cria automaticamente:

```text
resultados/nova_ordens_DD-MM-AAAA_HH-MM-SS.xlsx
```

Colunas:

- RE
- SIGLA
- TIPO
- CTE
- VINCULAR/ ACERTO
- ORDEM
- SITUAÇÃO

A situação das ordens geradas é `AUTORIZADO`, com fundo verde. O cabeçalho recebe fundo azul-claro.

## 7. Instalação no Windows

Dentro da pasta do projeto:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Depois execute:

```bat
iniciar_windows.bat
```

## 8. Instalação no Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
chmod +x iniciar_linux.sh
./iniciar_linux.sh
```

## Observação

Os valores fixos do formulário foram mantidos conforme os testes:

- Conta corrente: 0153080
- Observação: bag
- Conteúdo: bag - malote
- Volumes: 1
- Peso: 1,00
- Valor da coleta: 13,20
- Número da nota: dec
- Série: 0
- Valor da nota: 100,00
- Modalidade: CORPORATE
