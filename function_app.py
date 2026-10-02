import logging
import os
import pyodbc
import azure.functions as func
 
app = func.FunctionApp()


@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)

def extract_chamado(myTimer: func.TimerRequest) -> None:

    #capturar variaveis de ambiente
    host_sql = os.getenv("HOST")
    database_sql = os.getenv("DATABASE")
    user_sql = os.getenv("USER")
    pass_sql = os.getenv("PASSWORD")


    #string de conexao com PYODBC AZURE DB SQL

    conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={host_sql};"
            f"DATABASE={database_sql};"
            f"UID={user_sql};"
            f"PWD={pass_sql};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )

    try:
            conexao = pyodbc.connect(conn_str)
            cursor = conexao.cursor()

            cursor.execute("SELECT TOP 10 * FROM categoria")
            colunas = [coluna[0] for coluna in cursor.description]
            linhas = cursor.fetchall()

            logging.info(f"[extract_categoria] {len(linhas)} registro(s) encontrado(s):")
            for linha in linhas:
                registro = dict(zip(colunas, linha))
                logging.info(f"[extract_categoria] {registro}")

            cursor.close()
            conexao.close()

    except Exception as erro:
            logging.error(f"[extract_categoria] Erro ao conectar/consultar o banco: {erro}")




