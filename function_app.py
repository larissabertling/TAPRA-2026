import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
import pyodbc
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()


def salvar_no_bronze(tabela, colunas, rows):
    """Grava os dados da tabela como JSON no container bronze."""
    storage_conn = os.getenv("STORAGE_CONNECTION_STRING")
    container_name = os.getenv("CONTAINER_NAME", "bronze")

    registros = [dict(zip(colunas, row)) for row in rows]
    conteudo = json.dumps(registros, default=str, ensure_ascii=False)

    agora = datetime.now(timezone.utc)
    caminho = f"{tabela}/{agora:%Y-%m-%d}/{tabela}_{agora:%H%M%S}.json"

    blob_service = BlobServiceClient.from_connection_string(storage_conn)
    container = blob_service.get_container_client(container_name)
    container.upload_blob(name=caminho, data=conteudo, overwrite=True)
    logging.info(f"{len(registros)} registros de itsm.{tabela} salvos em {caminho}")


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_chamado(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.chamado")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("chamado", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.chamado: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_analista(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.analista")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("analista", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.analista: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_categoria(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.categoria")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("categoria", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.categoria: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_chamado_status_historico(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.chamado_status_historico")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("chamado_status_historico", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.chamado_status_historico: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_cliente_organizacao(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.cliente_organizacao")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("cliente_organizacao", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.cliente_organizacao: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_csat_avaliacao(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.csat_avaliacao")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("csat_avaliacao", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.csat_avaliacao: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 0 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_fila(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.fila")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("fila", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.fila: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_sla(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.sla")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("sla", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.sla: {str(e)}")
        raise


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def extract_solicitante(myTimer: func.TimerRequest) -> None:
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host_sql};"
        f"DATABASE={database_sql};"
        f"UID={user_sql};"
        f"PWD={pass_sql};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from itsm.solicitante")
            rows = cursor.fetchall()
            colunas = [c[0] for c in cursor.description]
            salvar_no_bronze("solicitante", colunas, rows)
    except Exception as e:
        logging.error(f"Erro ao ler itsm.solicitante: {str(e)}")
        raise