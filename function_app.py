import logging
import os

import azure.functions as func
import requests

app = func.FunctionApp()


# ---------------------------------------------------------------------------
# 1) TIMER TRIGGER - apenas imprime um log no terminal
#    Roda a cada 1 minuto (formato cron do Azure: seg min hora dia mes dia-semana)
# ---------------------------------------------------------------------------
@app.timer_trigger(
    schedule="0 */1 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def TimerLogOnly(myTimer: func.TimerRequest) -> None:
    logging.info("[TimerLogOnly] Timer trigger executado com sucesso!")


# ---------------------------------------------------------------------------
# 2) HTTP TRIGGER - recebe um parametro via GET na URL e imprime na tela
#    Exemplo de chamada: http://localhost:7071/api/HttpEcho?nome=Joao
# ---------------------------------------------------------------------------
@app.route(route="HttpEcho", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def HttpEcho(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[HttpEcho] Requisicao HTTP recebida.")

    nome = req.params.get("nome")

    if not nome:
        return func.HttpResponse(
            "Envie um parametro 'nome' na URL. Exemplo: ?nome=Joao",
            status_code=400,
        )

    mensagem = f"Voce enviou: {nome} -- processado pela HttpEcho!"
    logging.info(f"[HttpEcho] {mensagem}")

    return func.HttpResponse(mensagem, status_code=200)


# ---------------------------------------------------------------------------
# 3) TIMER TRIGGER - faz uma chamada HTTP para a function HttpEcho
#    e imprime no log a resposta recebida (parametro + texto de identificacao)
#    Roda a cada 2 minutos, para dar tempo da funcao acima ja estar no ar.
# ---------------------------------------------------------------------------
@app.timer_trigger(
    schedule="0 */2 * * * *",
    arg_name="myTimer2",
    run_on_startup=False,
    use_monitor=False,
)
def TimerCallsHttp(myTimer2: func.TimerRequest) -> None:
    logging.info("[TimerCallsHttp] Iniciando chamada HTTP para a HttpEcho...")

    base_url = os.environ.get("HTTP_ECHO_URL", "http://localhost:7071/api/HttpEcho")
    parametro_enviado = "TAPRA-2026"

    try:
        response = requests.get(
            base_url, params={"nome": parametro_enviado}, timeout=10
        )
        logging.info(f"[TimerCallsHttp] Resposta recebida: {response.text}")
    except Exception as erro:
        logging.error(f"[TimerCallsHttp] Erro ao chamar a HttpEcho: {erro}")
