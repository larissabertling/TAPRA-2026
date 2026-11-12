import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
import pyodbc
from azure.storage.blob import BlobServiceClient

from carga import executar_carga

app = func.FunctionApp()


def conectar_origem():
    """Conecta no banco de origem usando apenas variáveis de ambiente."""
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['SQL_HOST']};"
        f"DATABASE={os.environ['SQL_DATABASE']};"
        f"UID={os.environ['SQL_USER']};"
        f"PWD={os.environ['SQL_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


def salvar_no_bronze(tabela, colunas, rows):
    """Grava os dados da tabela como JSON no container bronze."""
    storage_conn = os.environ["STORAGE_CONNECTION_STRING"]
    container_name = os.getenv("CONTAINER_NAME", "bronze")

    registros = [dict(zip(colunas, row, strict=True)) for row in rows]
    conteudo = json.dumps(registros, default=str, ensure_ascii=False)

    agora = datetime.now(timezone.utc)
    caminho = f"{tabela}/{agora:%Y-%m-%d}/{tabela}_{agora:%H%M%S}.json"

    blob_service = BlobServiceClient.from_connection_string(storage_conn)
    container = blob_service.get_container_client(container_name)
    container.upload_blob(name=caminho, data=conteudo, overwrite=True)
    logging.info(f"{len(registros)} registros de itsm.{tabela} salvos em {caminho}")


def extrair_tabela(tabela):
    """Lê itsm.<tabela> inteira do banco de origem e grava no bronze."""
    try:
        with conectar_origem() as conn:
            cursor = conn.cursor()
            cursor.execute(f"select * from itsm.{tabela}")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze(tabela, colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.{tabela}: {str(e)}")
        raise


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_analista(myTimer: func.TimerRequest) -> None:
    extrair_tabela("analista")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_categoria(myTimer: func.TimerRequest) -> None:
    extrair_tabela("categoria")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_chamado(myTimer: func.TimerRequest) -> None:
    extrair_tabela("chamado")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_chamado_sla(myTimer: func.TimerRequest) -> None:  # NOVA
    extrair_tabela("chamado_sla")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_chamado_status_historico(myTimer: func.TimerRequest) -> None:
    extrair_tabela("chamado_status_historico")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_cliente_organizacao(myTimer: func.TimerRequest) -> None:
    extrair_tabela("cliente_organizacao")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_csat_avaliacao(myTimer: func.TimerRequest) -> None:
    extrair_tabela("csat_avaliacao")


@app.timer_trigger(schedule="0 0 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_fila(myTimer: func.TimerRequest) -> None:
    extrair_tabela("fila")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_sla(myTimer: func.TimerRequest) -> None:
    extrair_tabela("sla")


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_solicitante(myTimer: func.TimerRequest) -> None:
    extrair_tabela("solicitante")


@app.timer_trigger(
    schedule="0 0 6 * * *",  # uma vez ao dia, 06:00 UTC (03:00 em Brasília)
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def load_destino(myTimer: func.TimerRequest) -> None:
    """Popula as tabelas do banco de destino a partir do bronze, respeitando as FKs."""
    try:
        executar_carga()
    except Exception as e:
        logging.error(f"Erro ao popular o banco de destino: {str(e)}")
        raise
