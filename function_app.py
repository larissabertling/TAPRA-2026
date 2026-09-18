import logging
import os
import requests
import azure.functions as func

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False
)
def TimerLogOnly(myTimer: func.TimerRequest) -> None:
    logging.info("Timer executado com sucesso!")


@app.route(
    route="HttpEcho",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def HttpEcho(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Requisição HTTP recebida.")

    nome = req.params.get("nome")

    if not nome:
        return func.HttpResponse(
            "Envie um parametro 'nome' na URL. Exemplo: ?nome=Joao",
            status_code=400
        )

    mensagem = f"Voce enviou: {nome} - processado pela HttpEcho!"

    logging.info(mensagem)

    return func.HttpResponse(
        mensagem,
        status_code=200
    )


# Timer que chama a função HTTP
@app.timer_trigger(
    schedule="0 */2 * * * *",
    arg_name="myTimer2",
    run_on_startup=False,
    use_monitor=False
)
def TimerCallsHttp(myTimer2: func.TimerRequest) -> None:

    logging.info("Iniciando chamada HTTP para a HttpEcho...")

    url = os.environ.get(
        "HTTP_ECHO_URL",
        "http://localhost:7071/api/HttpEcho"
    )

    nome = "TAPRA-2026"

    try:
        resposta = requests.get(
            url,
            params={"nome": nome},
            timeout=10
        )

        logging.info(f"Resposta recebida: {resposta.text}")

    except Exception as erro:
        logging.error(f"Erro ao chamar a HttpEcho: {erro}")
