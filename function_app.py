import logging
import os

import azure.functions as func
import pymssql

app = func.FunctionApp()


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


# ATIVIDADE 2B: captura dos dados de TODAS as tabelas do banco de origem (itsm)
@app.timer_trigger(
    schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def timer_trigger_captura_todas_tabelas(myTimer: func.TimerRequest) -> None:
    logging.info("Iniciando captura de todas as tabelas do banco.")

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
        cursor = conn.cursor()

        # Descobre as tabelas direto do banco, assim nenhuma fica de fora
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME "
            "FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_SCHEMA, TABLE_NAME"
        )
        tabelas = cursor.fetchall()
        logging.info(f"Tabelas encontradas: {len(tabelas)}")

        for schema, tabela in tabelas:
            try:
                # Nomes vêm do próprio banco; colchetes protegem o identificador
                cursor.execute(f"SELECT * FROM [{schema}].[{tabela}]")
                total = 0
                while True:
                    lote = cursor.fetchmany(1000)
                    if not lote:
                        break
                    total += len(lote)
                    # aqui entra o processamento/gravação dos dados, se necessário
                logging.info(f"Tabela {schema}.{tabela}: {total} registros capturados")
            except Exception:
                logging.exception(f"Erro ao capturar a tabela {schema}.{tabela}")

    except Exception:
        logging.exception("Erro na captura de todas as tabelas.")
        raise
    finally:
        if conn:
            conn.close()
            logging.info("Conexão encerrada.")