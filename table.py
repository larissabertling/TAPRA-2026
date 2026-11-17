import argparse
import csv
import io
import json
import os
import re

FONTE = "itsm"

TABELAS = [
    "chamado",
    "analista",
    "categoria",
    "chamado_sla",
    "chamado_status_historico",
    "cliente_organizacao",
    "csat_avaliacao",
    "fila",
    "sla",
    "solicitante",
]

RE_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_INT = re.compile(r"^-?\d+$")
RE_DEC = re.compile(r"^-?\d+\.\d+$")


def tipo_valor(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return "BIT"
    if isinstance(v, int):
        return "BIGINT" if abs(v) > 2_147_483_647 else "INT"
    if isinstance(v, float):
        return "DECIMAL(18,4)"
    s = str(v).strip()
    if RE_DATETIME.match(s):
        return "DATETIME2"
    if RE_DATE.match(s):
        return "DATE"
    if RE_INT.match(s) and len(s) < 10 and not s.startswith("0"):
        return "INT"
    if RE_DEC.match(s):
        return "DECIMAL(18,4)"
    return f"STR:{len(s)}"


def tipo_coluna(valores):
    tipos = {t for t in (tipo_valor(v) for v in valores) if t}
    if not tipos:
        return "NVARCHAR(255)"
    strs = [int(t[4:]) for t in tipos if t.startswith("STR:")]
    if strs or len(tipos) > 1 and not tipos <= {"INT", "BIGINT", "DECIMAL(18,4)"}:
        maior = max(strs) if strs else 50
        if maior > 1000:
            return "NVARCHAR(MAX)"
        return f"NVARCHAR({max(50, ((maior // 50) + 1) * 50 * 2)})"
    if "DECIMAL(18,4)" in tipos:
        return "DECIMAL(18,4)"
    if "BIGINT" in tipos:
        return "BIGINT"
    return tipos.pop()


def ler_registros(nome_arquivo, conteudo):
    if nome_arquivo.lower().endswith(".json"):
        dados = json.loads(conteudo)
        return dados if isinstance(dados, list) else [dados]
    return list(csv.DictReader(io.StringIO(conteudo)))


def carregar_local(pasta):
    out = {}
    for t in TABELAS:
        base = os.path.join(pasta, t)
        arqs = []
        for raiz, _, fs in os.walk(base):
            arqs += [os.path.join(raiz, f) for f in fs if f.lower().endswith((".json", ".csv"))]
        if arqs:
            ultimo = sorted(arqs)[-1]
            with open(ultimo, encoding="utf-8-sig") as f:
                out[t] = ler_registros(ultimo, f.read())
    return out


def carregar_storage():
    from azure.storage.blob import BlobServiceClient

    svc = BlobServiceClient.from_connection_string(os.environ["STORAGE_CONNECTION_STRING"])
    cont = svc.get_container_client(os.getenv("CONTAINER_NAME", "bronze"))
    out = {}
    for t in TABELAS:
        blobs = sorted(b.name for b in cont.list_blobs(name_starts_with=f"{FONTE}/{t}/"))
        if blobs:
            conteudo = cont.download_blob(blobs[-1]).readall().decode("utf-8-sig")
            out[t] = ler_registros(blobs[-1], conteudo)
    return out


def gerar_sql(dados, schema="dbo"):
    linhas = []
    for t in TABELAS:
        regs = dados.get(t)
        if not regs:
            linhas.append(f"-- ATENÇÃO: nenhum arquivo encontrado para '{t}'\n")
            continue
        colunas = list(regs[0].keys())
        defs = []
        for c in colunas:
            tipo = tipo_coluna([r.get(c) for r in regs])
            sem_vazios = all(r.get(c) not in (None, "") for r in regs)
            nulo = "NOT NULL" if c.lower().startswith("id") and sem_vazios else "NULL"
            defs.append(f"    [{c}] {tipo} {nulo}")
        linhas.append(
            f"IF OBJECT_ID('{schema}.{t}', 'U') IS NULL\n"
            f"CREATE TABLE {schema}.{t} (\n" + ",\n".join(defs) + "\n);\nGO\n"
        )
    return "\n".join(linhas)


def executar_sql(sql):
    """Executa o script no banco de destino (variáveis DEST_*), separando os blocos por GO."""
    import pymssql

    conn = pymssql.connect(
        server=os.environ["DEST_HOST"],
        user=os.environ["DEST_USER"],
        password=os.environ["DEST_PASSWORD"],
        database=os.environ["DEST_DATABASE"],
        port=os.getenv("DEST_PORT", "1433"),
        login_timeout=30,
    )
    try:
        cursor = conn.cursor()
        for bloco in re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE):
            if bloco.strip():
                cursor.execute(bloco)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta")
    ap.add_argument("--storage", action="store_true")
    ap.add_argument("--saida", default="create_tables.sql")
    ap.add_argument("--executar", action="store_true", help="cria as tabelas no banco de destino")
    a = ap.parse_args()
    if not a.pasta and not a.storage:
        ap.error("use --pasta <dir> ou --storage")
    dados = carregar_storage() if a.storage else carregar_local(a.pasta)
    with open(a.saida, "w", encoding="utf-8") as f:
        f.write(gerar_sql(dados))
    print(f"OK: {a.saida} gerado com {len(dados)} tabela(s).")
    if a.executar:
        with open(a.saida, encoding="utf-8") as f:
            executar_sql(f.read())
        print("OK: tabelas criadas no banco de destino.")
