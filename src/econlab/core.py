from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("ECONLAB_ROOT", Path(__file__).resolve().parents[2])).resolve()
DB = ROOT / "data/econ_lab.db"
RAW = ROOT / "data/raw"
OUT = ROOT / "outputs"
SCHEMA = Path(__file__).resolve().parents[2] / "db/schema.sql"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def audit(tool: str, outcome: str, **details) -> None:
    folder = ROOT / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "audit.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"ts": now(), "tool": tool, "outcome": outcome, **details},
                                ensure_ascii=False, allow_nan=False) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_check(code: str) -> None:
    if code not in catalog():
        raise ValueError(f"Serie fora do catalogo publico: {code}")


def catalog() -> dict:
    path = RAW / "catalog.json"
    if not path.is_file():
        raise FileNotFoundError("Cache ausente: execute econlab download.")
    return json.loads(path.read_text(encoding="utf-8"))


def monthly(frame: pd.DataFrame, minimum: int = 1) -> pd.DataFrame:
    if set(frame.columns) != {"data_ref", "valor"} or len(frame) < minimum:
        raise ValueError(f"Esperadas colunas data_ref/valor e pelo menos {minimum} linhas.")
    df = frame.copy()
    parsed = pd.to_datetime(df.data_ref, format="%Y-%m-%d", errors="raise")
    if not all(parsed.dt.strftime("%Y-%m-%d") == df.data_ref):
        raise ValueError("Datas devem estar em ISO estrito.")
    if not all(parsed.dt.day == 1) or parsed.duplicated().any():
        raise ValueError("Datas mensais devem ser unicas e no primeiro dia.")
    df["valor"] = pd.to_numeric(df.valor, errors="raise")
    if df.valor.isna().any() or not all(math.isfinite(float(x)) for x in df.valor):
        raise ValueError("Valores nulos ou nao finitos.")
    df = df.sort_values("data_ref").reset_index(drop=True)
    expected = pd.date_range(df.data_ref.iloc[0], df.data_ref.iloc[-1], freq="MS")
    if list(expected.strftime("%Y-%m-%d")) != list(df.data_ref):
        raise ValueError("Lacuna no calendario mensal; nao houve preenchimento.")
    return df


def cache(code: str) -> tuple[pd.DataFrame, dict]:
    code_check(code)
    meta = catalog()[code]
    required = {"nome", "unidade", "frequencia", "ajuste_sazonal", "url",
                "extraido_em", "sha256", "fonte", "metadata_url", "tema"}
    if not required <= meta.keys() or meta["frequencia"] != "M":
        raise ValueError("Metadados incompletos ou frequencia nao mensal.")
    if meta["ajuste_sazonal"] not in ("sim", "nao", "nao_aplicavel"):
        raise ValueError("Ajuste sazonal indefinido.")
    path = RAW / f"{code}.csv"
    if digest(path) != meta["sha256"]:
        raise ValueError("Checksum do cache diverge do catalogo.")
    for suffix in ("response", "metadata"):
        evidence = RAW / f"{code}.{suffix}.json"
        if digest(evidence) != meta[f"{suffix}_sha256"]:
            raise ValueError(f"Checksum da evidencia {suffix} diverge do catalogo.")
    return monthly(pd.read_csv(path)), meta


def connect(*, write: bool = False) -> sqlite3.Connection:
    if not DB.is_file():
        raise FileNotFoundError(f"Base inexistente: {DB}; execute econlab reset.")
    con = sqlite3.connect(f"{DB.as_uri()}?mode={'rw' if write else 'ro'}",
                          uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.enable_load_extension(False)
    if not write:
        con.execute("PRAGMA query_only=ON")
    return con


def sql_read(sql: str, limit: int = 1000) -> dict:
    if not 1 <= limit <= 5000 or len(sql) > 20000:
        raise ValueError("Limites: 1..5000 linhas, SQL ate 20000 caracteres.")
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_RECURSIVE}
    functions = {"count", "min", "max", "avg", "sum", "round", "abs", "coalesce",
                 "substr", "length", "lower", "upper", "date", "strftime", "like"}
    tables = {"fontes", "series", "cargas", "observacoes", "metadados",
              "vw_ultima_observacao", "sqlite_master"}

    def authorize(action, arg1, arg2, database, source):
        if action == sqlite3.SQLITE_FUNCTION:
            return sqlite3.SQLITE_OK if (arg2 or "").lower() in functions else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_READ:
            if database is None and arg2 == "":
                # SQLite reports a column-free scan of an ephemeral CTE this way.
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_OK if arg1 in tables else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY

    start = time.monotonic()
    try:
        with closing(connect()) as con:
            con.set_authorizer(authorize)
            con.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 100000)
            con.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 20000)
            con.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 100)
            steps = 0

            def progress():
                nonlocal steps
                steps += 1
                return int(steps > 2000 or time.monotonic() - start > 2)

            con.set_progress_handler(progress, 1000)
            cursor = con.execute(sql)
            if cursor.description is None:
                raise ValueError("Somente consultas com resultado.")
            rows, size, reason = [], 0, None
            for row in cursor:
                record = dict(row)
                size += len(json.dumps(record, ensure_ascii=False, allow_nan=False).encode())
                if len(rows) >= limit or size > 2000000:
                    reason = "limite_linhas" if len(rows) >= limit else "limite_bytes"
                    break
                rows.append(record)
            result = {"rows": rows, "truncated": reason is not None, "limit_reason": reason}
        audit("consulta_sql", "ok", linhas=len(result["rows"]))
        return result
    except (sqlite3.Error, ValueError, FileNotFoundError) as exc:
        audit("consulta_sql", "error", erro=str(exc))
        raise


def series(code: str) -> tuple[pd.DataFrame, dict]:
    with closing(connect()) as con:
        row = con.execute("SELECT * FROM series WHERE codigo_serie=?", (code,)).fetchone()
        if row is None:
            raise ValueError(f"Serie nao carregada: {code}")
        values = con.execute("SELECT data_ref,valor FROM observacoes WHERE codigo_serie=? "
                             "ORDER BY data_ref", (code,)).fetchall()
        metadata = {r["chave"]: json.loads(r["valor"]) for r in con.execute(
            "SELECT chave,valor FROM metadados WHERE codigo_serie=?", (code,))}
    return monthly(pd.DataFrame([dict(r) for r in values])), {**dict(row), **metadata}


def proposal(code: str) -> dict:
    df, meta = cache(code)
    with closing(connect()) as con:
        revision = [tuple(r) for r in con.execute(
            "SELECT id_carga,codigo_serie,sha256 FROM cargas ORDER BY id_carga")]
    body = {"banco": str(DB), "codigo": code, "linhas": len(df), "inicio": df.data_ref.iloc[0],
            "fim": df.data_ref.iloc[-1], "metadados": meta, "revisao": revision}
    body["proposta"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    body["autorizacao"] = "Necessaria no terminal humano; o MCP nao pode conceder."
    return body


def approve(code: str, expected: str, actor: str) -> dict:
    current = proposal(code)
    if current["proposta"] != expected or not actor.strip():
        raise ValueError("Proposta divergente ou ator ausente.")
    with closing(connect(write=True)) as con, con:
        cur = con.execute(
            "INSERT INTO autorizacoes(proposta,ator,expira_em) VALUES (?,?,?) "
            "ON CONFLICT(proposta) DO UPDATE SET ator=excluded.ator,expira_em=excluded.expira_em "
            "WHERE autorizacoes.consumida=0 AND autorizacoes.expira_em < ?",
            (expected, actor, time.time() + 600, time.time()))
        if cur.rowcount != 1:
            raise PermissionError("Autorizacao ainda vigente ou ja consumida; nao renovada.")
    audit("autorizar", "ok", codigo=code, proposta=expected, ator=actor)
    return {"proposta": expected, "ator": actor, "validade_segundos": 600}


def _insert(con: sqlite3.Connection, code: str, df: pd.DataFrame, meta: dict, actor: str) -> dict:
    existing = con.execute("SELECT id_carga FROM cargas WHERE codigo_serie=? AND sha256=?",
                           (code, meta["sha256"])).fetchone()
    if existing:
        return {"codigo": code, "status": "idempotente", "id_carga": existing[0],
                "linhas": len(df)}
    if con.execute("SELECT 1 FROM series WHERE codigo_serie=?", (code,)).fetchone():
        raise ValueError("Cache revisado: reset explicito necessario; sem sobrescrita silenciosa.")
    source = 1 if meta["fonte"] == "BCB" else 2
    con.execute("INSERT INTO series VALUES (?,?,?,?,?,?)",
                (code, source, meta["nome"], meta["unidade"], "M", meta["tema"]))
    cur = con.execute("INSERT INTO cargas(codigo_serie,origem,sha256,extraido_em,"
                      "executado_em,linhas,status,ator) VALUES (?,?,?,?,?,?,'ok',?)",
                      (code, meta["url"], meta["sha256"], meta["extraido_em"],
                       now(), len(df), actor))
    con.executemany("INSERT INTO observacoes VALUES (?,?,?,?)",
                    [(code, r.data_ref, float(r.valor), cur.lastrowid)
                     for r in df.itertuples()])
    con.executemany("INSERT INTO metadados VALUES (?,?,?)",
                    [(code, k, json.dumps(v, ensure_ascii=False)) for k, v in meta.items()])
    return {"codigo": code, "status": "ok", "id_carga": cur.lastrowid, "linhas": len(df)}


def ingest(code: str, expected: str) -> dict:
    try:
        current = proposal(code)
        if current["proposta"] != expected:
            raise ValueError("Proposta alterada: valide e autorize novamente.")
        df, meta = cache(code)
        with closing(connect(write=True)) as con, con:
            con.execute("BEGIN IMMEDIATE")
            revision = [list(r) for r in con.execute(
                "SELECT id_carga,codigo_serie,sha256 FROM cargas ORDER BY id_carga")]
            if revision != [list(r) for r in current["revisao"]]:
                raise ValueError("Base mudou antes da transacao; valide novamente.")
            auth = con.execute("SELECT * FROM autorizacoes WHERE proposta=?", (expected,)).fetchone()
            if not auth or auth["consumida"] or auth["expira_em"] < time.time():
                raise PermissionError("Autorizacao ausente, expirada ou consumida.")
            result = _insert(con, code, df, meta, auth["ator"])
            con.execute("UPDATE autorizacoes SET consumida=1 WHERE proposta=?", (expected,))
        audit("ingerir_serie_cache", "ok", **result, ator=auth["ator"])
        return result
    except (ValueError, PermissionError, sqlite3.Error, OSError) as exc:
        audit("ingerir_serie_cache", "error", codigo=code, erro=str(exc))
        raise


def reset() -> dict:
    validated = {code: cache(code) for code in catalog() if code != "IBGE_PIMPF"}
    if len(validated) != 7:
        raise ValueError("Reset exige exatamente sete series iniciais.")
    DB.parent.mkdir(parents=True, exist_ok=True)
    target = DB.with_suffix(".building.db")
    if target.exists():
        raise FileExistsError(f"Arquivo de construcao anterior: {target}; inspecione antes de remover.")
    try:
        with closing(sqlite3.connect(target)) as con, con:
            con.executescript(SCHEMA.read_text(encoding="utf-8"))
            con.executemany("INSERT INTO fontes VALUES (?,?,?,?)", [
                (1, "BCB - SGS", "https://www.bcb.gov.br", "Dados publicos; citar fonte e observar termos da origem"),
                (2, "IBGE - SIDRA", "https://sidra.ibge.gov.br", "Dados publicos; citar IBGE"),
            ])
            for code, (df, meta) in validated.items():
                _insert(con, code, df, meta, "setup-explicito")
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Falha na integridade da base preparada.")
        target.replace(DB)
    except Exception:
        if target.exists():
            target.unlink()
        raise
    with closing(connect()) as source, closing(sqlite3.connect(DB.with_name("econ_lab_backup.db"))) as backup:
        source.backup(backup)
    audit("reset", "ok", series=7, pim_no_cache=True)
    return {"series": 7, "IBGE_PIMPF": "somente cache", "db": str(DB)}
