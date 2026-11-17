import base64
import json
import logging
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import azure.functions as func
import pymssql
from azure.storage.blob import ContainerClient, ContentSettings

from carga import executar_carga

app = func.FunctionApp()

FONTE = "itsm"


def get_bronze_container() -> ContainerClient:
    """Cliente do container bronze. A conexão vem de variável de ambiente."""
    return ContainerClient.from_connection_string(
        conn_str=os.environ["STORAGE_CONNECTION_STRING"],
        container_name=os.getenv("CONTAINER_NAME", "bronze"),
    )


def montar_caminho_bronze(entidade: str, momento: datetime) -> str:
    """itsm/<entidade>/ano=AAAA/mes=MM/dia=DD/<entidade>_AAAAMMDDTHHMMSSZ.json"""
    carimbo = momento.strftime("%Y%m%dT%H%M%SZ")
    return (
        f"{FONTE}/{entidade}/"
        f"ano={momento:%Y}/mes={momento:%m}/dia={momento:%d}/"
        f"{entidade}_{carimbo}.json"
    )


def serializar_valor(valor):
    """Converte tipos do SQL Server que o json não conhece."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, UUID):
        return str(valor)
    if isinstance(valor, (bytes, bytearray)):
        return base64.b64encode(valor).decode("ascii")
    raise TypeError(f"Tipo não serializável: {type(valor)}")


@app.timer_trigger(
    schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_hello(myTimer: func.TimerRequest) -> None:
    logging.info("Hello world")


@app.route(route="http_trigger", auth_level=func.AuthLevel.ANONYMOUS)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    name = req.params.get("name")

    if name:
        return func.HttpResponse(
            f"Hello, {name}. This HTTP triggered function executed successfully."
        )
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. "
            "Pass a name in the query string or in the request body "
            "for a personalized response.",
            status_code=200,
        )


@app.timer_trigger(
    schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_variaveis(myTimer: func.TimerRequest) -> None:
    servidor = os.getenv("SQL_HOST")
    banco_dados = os.getenv("SQL_DATABASE")
    usuario = os.getenv("SQL_USER")
    senha = os.getenv("SQL_PASSWORD")

    logging.info(f"Servidor: {servidor}")
    logging.info(f"Banco de Dados: {banco_dados}")
    logging.info(f"Usuário: {usuario}")
    logging.info(f"Senha definida: {senha is not None}")


@app.timer_trigger(
    schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_cicd(myTimer: func.TimerRequest) -> None:
    servidor = os.getenv("SQL_HOST")
    banco_dados = os.getenv("SQL_DATABASE")
    usuario = os.getenv("SQL_USER")
    senha = os.getenv("SQL_PASSWORD")

    logging.info(f"Servidor: {servidor}")
    logging.info(f"Banco de Dados: {banco_dados}")
    logging.info(f"Usuário: {usuario}")
    logging.info(f"Senha definida: {senha is not None}")


# ATIVIDADE 2B: captura dos dados de UMA tabela do banco de origem (itsm.chamado)
@app.timer_trigger(
    schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_captura_chamado(myTimer: func.TimerRequest) -> None:
    logging.info("Iniciando captura da tabela 'chamado'.")

    conn = None
    try:
        conn = pymssql.connect(
            server=os.getenv("SQL_HOST"),
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            database=os.getenv("SQL_DATABASE"),
            port=os.getenv("SQL_PORT", "1433"),
            login_timeout=15,
        )
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT TOP 100 * FROM chamado")
        linhas = cursor.fetchall()

        logging.info(f"Registros capturados: {len(linhas)}")
        for linha in linhas[:5]:
            logging.info(f"Amostra: {linha}")

    except Exception:
        logging.exception("Erro ao capturar dados da tabela 'chamado'.")
        raise
    finally:
        if conn:
            conn.close()
            logging.info("Conexão encerrada.")


@app.timer_trigger(
    schedule="0 0 8 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_captura_todas_tabelas(myTimer: func.TimerRequest) -> None:
    logging.info("Iniciando extração de todas as tabelas para o Data Lake.")

    agora = datetime.now(timezone.utc)  # mesmo instante para todas as tabelas desta execução
    container = get_bronze_container()

    conn = None
    try:
        conn = pymssql.connect(
            server=os.getenv("SQL_HOST"),
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            database=os.getenv("SQL_DATABASE"),
            port=os.getenv("SQL_PORT", "1433"),
            login_timeout=15,
        )
        cursor = conn.cursor(as_dict=True)

        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME "
            "FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_SCHEMA, TABLE_NAME"
        )
        tabelas = [(linha["TABLE_SCHEMA"], linha["TABLE_NAME"]) for linha in cursor.fetchall()]
        logging.info(f"Tabelas encontradas: {len(tabelas)}")

        for schema, tabela in tabelas:
            try:
                cursor.execute(f"SELECT * FROM [{schema}].[{tabela}]")
                registros = cursor.fetchall()

                caminho = montar_caminho_bronze(tabela, agora)
                container.upload_blob(
                    name=caminho,
                    data=json.dumps(registros, default=serializar_valor, ensure_ascii=False),
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/json"),
                )
                logging.info(f"{schema}.{tabela}: {len(registros)} registros -> {caminho}")
            except Exception:
                logging.exception(f"Erro ao extrair/gravar a tabela {schema}.{tabela}")

    except Exception:
        logging.exception("Erro na extração de todas as tabelas.")
        raise
    finally:
        if conn:
            conn.close()
            logging.info("Conexão encerrada.")


@app.timer_trigger(
    schedule="0 0 9 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_carga_destino(myTimer: func.TimerRequest) -> None:
    logging.info("Iniciando carga diária no banco de destino.")
    executar_carga()
    logging.info("Carga diária finalizada.")
