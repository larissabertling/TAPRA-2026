import json
import logging
import os

import pyodbc
from azure.storage.blob import BlobServiceClient

ORDEM_CARGA = [
    "sla",
    "categoria",
    "fila",
    "cliente_organizacao",
    "analista",
    "solicitante",
    "chamado",
    "chamado_sla",
    "chamado_status_historico",
    "csat_avaliacao",
]

TAMANHO_LOTE = 1000


def conectar_destino():
    """Abre conexão com o banco de destino usando variáveis de ambiente."""
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['DEST_HOST']};"
        f"DATABASE={os.environ['DEST_DATABASE']};"
        f"UID={os.environ['DEST_USER']};"
        f"PWD={os.environ['DEST_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str, autocommit=False)


def ler_ultimo_bronze(tabela):
    """Lê o arquivo JSON mais recente da tabela no container bronze."""
    svc = BlobServiceClient.from_connection_string(os.environ["STORAGE_CONNECTION_STRING"])
    container = svc.get_container_client(os.getenv("CONTAINER_NAME", "bronze"))
    blobs = sorted(b.name for b in container.list_blobs(name_starts_with=f"{tabela}/"))
    if not blobs:
        return None
    conteudo = container.download_blob(blobs[-1]).readall().decode("utf-8-sig")
    dados = json.loads(conteudo)
    logging.info(f"Bronze: lendo {blobs[-1]}")
    return dados if isinstance(dados, list) else [dados]


def _ident(nome):
    """Escapa identificador SQL Server: [nome]."""
    return "[" + str(nome).replace("]", "]]") + "]"


def montar_insert(schema, tabela, colunas):
    cols = ", ".join(_ident(c) for c in colunas)
    params = ", ".join("?" for _ in colunas)
    return f"INSERT INTO {_ident(schema)}.{_ident(tabela)} ({cols}) VALUES ({params})"


def _tem_identity(cursor, schema, tabela):
    cursor.execute(
        "SELECT OBJECTPROPERTY(OBJECT_ID(?), 'TableHasIdentity')",
        f"{_ident(schema)}.{_ident(tabela)}",
    )
    return cursor.fetchone()[0] == 1


def _inserir(cursor, schema, tabela, registros):
    colunas = list(registros[0].keys())
    sql = montar_insert(schema, tabela, colunas)
    valores = [tuple(r.get(c) for c in colunas) for r in registros]

    tabela_sql = f"{_ident(schema)}.{_ident(tabela)}"
    identity = _tem_identity(cursor, schema, tabela)
    if identity:
        cursor.execute(f"SET IDENTITY_INSERT {tabela_sql} ON")

    cursor.fast_executemany = True
    for i in range(0, len(valores), TAMANHO_LOTE):
        cursor.executemany(sql, valores[i : i + TAMANHO_LOTE])

    if identity:
        cursor.execute(f"SET IDENTITY_INSERT {tabela_sql} OFF")


def carregar_destino(dados_por_tabela, conn, schema="dbo"):
    """Substitui o conteúdo das tabelas do destino pelo snapshot do bronze.

    `dados_por_tabela`: dict {tabela: lista_de_registros}. Tabelas sem dados são ignoradas
    (e não são apagadas), para não perder informação por falta de arquivo no bronze.
    """
    tabelas = [t for t in ORDEM_CARGA if dados_por_tabela.get(t)]
    cursor = conn.cursor()
    try:
        for t in reversed(tabelas):
            cursor.execute(f"DELETE FROM {_ident(schema)}.{_ident(t)}")
        for t in tabelas:
            _inserir(cursor, schema, t, dados_por_tabela[t])

def executar_carga():
    """Lê o bronze, substitui o conteúdo do destino numa única transação e confirma."""
    dados = {}
    for t in ORDEM_CARGA:
        registros = ler_ultimo_bronze(t)
        if registros:
            dados[t] = registros
        else:
            logging.warning(f"Bronze sem arquivo para '{t}'; tabela ignorada na carga")

    if not dados:
        logging.warning("Nenhum dado no bronze; carga cancelada")
        return

    conn = conectar_destino()
    try:
        carregar_destino(dados, conn)
        conn.commit()
        logging.info(f"Carga concluída: {len(dados)} tabela(s)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
