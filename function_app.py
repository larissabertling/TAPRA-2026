import logging
import azure.functions as func
import os

app = func.FunctionApp()

@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)


def timer_trigger_hello(myTimer: func.TimerRequest) -> None:
        logging.info('Hello world')


@app.route(route="http_trigger", auth_level=func.AuthLevel.ANONYMOUS)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger_variaveis(myTimer: func.TimerRequest) -> None:
    servidor = os.getenv("SQL_HOST")
    banco_dados = os.getenv("SQL_DATABASE")
    usuario = os.getenv("SQL_USER")
    senha = os.getenv("SQL_PASSWORD")

    logging.info(f"Servidor: {servidor}")
    logging.info(f"Banco de Dados: {banco_dados}")
    logging.info(f"Usuário: {usuario}")
    logging.info(f"Senha definida: {senha is not None}")
