from __future__ import annotations

import json
import re
import html
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from econlab import core

START, END = "2022-01-01", "2025-12-01"
SGS = {
    433: ("IPCA - variacao mensal", "% a.m.", "inflacao", "nao", "IPCA"),
    189: ("IGP-M - variacao mensal", "% a.m.", "inflacao", "nao", "IGP"),
    4189: ("Selic acumulada no mes anualizada base 252", "% a.a.", "juros",
           "nao_aplicavel", "252"),
    3698: ("Cambio comercial venda - media mensal", "R$/US$", "externo",
           "nao_aplicavel", "venda"),
    24363: ("IBC-Br sem ajuste sazonal", "indice", "atividade", "nao", "IBC-Br"),
    24364: ("IBC-Br com ajuste sazonal", "indice", "atividade", "sim", "ajuste sazonal"),
}
SIDRA = {
    "IBGE_PMC": (8880, 7169, 11046, 56734, "volume", "PMC"),
    "IBGE_PIMPF": (8888, 12606, 544, 129314, "Indústria geral", "PIMPF"),
}


def fetch(url: str) -> tuple[object, str]:
    with requests.Session() as session:
        retry = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        response = session.get(url, timeout=(10, 40))
        response.raise_for_status()
        return response.json(), response.url


def store(code: str, df: pd.DataFrame, meta: dict, original: object, official: object) -> dict:
    df = core.monthly(df, minimum=48)
    if df.data_ref.iloc[0] != START or df.data_ref.iloc[-1] != END or len(df) != 48:
        raise ValueError(f"{code}: janela congelada 2022-2025 incompleta.")
    core.RAW.mkdir(parents=True, exist_ok=True)
    path = core.RAW / f"{code}.csv"
    df.to_csv(path, index=False)
    for suffix, obj in (("response", original), ("metadata", official)):
        (core.RAW / f"{code}.{suffix}.json").write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**meta, "frequencia": "M", "extraido_em": core.now(),
            "sha256": core.digest(path), "inicio": START, "fim": END,
            "response_sha256": core.digest(core.RAW / f"{code}.response.json"),
            "metadata_sha256": core.digest(core.RAW / f"{code}.metadata.json")}


def bcb(number: int, config: tuple) -> tuple[str, dict]:
    name, unit, topic, adjustment, keyword = config
    base = "https://www3.bcb.gov.br/sgspub/"
    metadata_url = (base + "consultarmetadados/consultarMetadadosSeries.paint"
                    f"?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada={number}")
    with requests.Session() as session:
        retry = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        page = session.get(metadata_url, timeout=(10, 40))
        page.raise_for_status()
        basic = session.get(base + "JSP/consultarmetadados/cmiDadosBasicos.jsp", timeout=(10, 40))
        basic.raise_for_status()
        text = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", basic.text)))
    expected_title = {433: "IPCA", 189: "IGP-M", 4189: "basis 252",
                      3698: "United States dollar (sale)", 24363: "Economic Activity Index",
                      24364: "seasonally adjusted"}[number]
    expected_unit = {433: "Monthly % var.", 189: "Monthly % var.", 4189: "% p.y.",
                     3698: "c.m.u./US$", 24363: "Index", 24364: "Index"}[number]
    if (f"series {number} " not in text or expected_title not in text
            or "Periodicity Monthly" not in text or f"Unit {expected_unit}" not in text):
        raise ValueError(f"Metadados oficiais SGS {number} nao confirmam selecao: {text}")
    official = {"selection_url": metadata_url, "basic_url": basic.url, "texto": text}
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{number}/dados"
           "?formato=json&dataInicial=01/01/2022&dataFinal=31/12/2025")
    response, url = fetch(url)
    df = pd.DataFrame(response)
    df["data_ref"] = pd.to_datetime(df["data"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d")
    meta = {"nome": name, "unidade": unit, "tema": topic, "ajuste_sazonal": adjustment,
            "fonte": "BCB", "url": url, "metadata_url": metadata_url,
            "titulo_oficial": text.split("Full name ")[1].split(" Short name")[0],
            "codigo_sgs": number, "unidade_oficial": expected_unit,
            "nota_unidade": "c.m.u./US$ equivale a R$/US$ na amostra pos-1994."
                           if number == 3698 else "Unidade mensal conforme pagina oficial SGS."}
    return f"BCB_{number}", store(f"BCB_{number}", df[["data_ref", "valor"]], meta, response, official)


def sidra(code: str, config: tuple) -> tuple[str, dict]:
    table, variable, classification, category, keyword, label = config
    metadata_url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{table}/metadados"
    official, _ = fetch(metadata_url)
    var = next(v for v in official["variaveis"] if v["id"] == variable)
    cat = next(c for c in official["classificacoes"] if c["id"] == classification)
    category_meta = next(c for c in cat["categorias"] if c["id"] == category)
    if keyword.casefold() not in category_meta["nome"].casefold():
        raise ValueError("Categoria SIDRA divergente.")
    if "ajuste sazonal" in var["nome"] or official["periodicidade"]["frequencia"] != "mensal":
        raise ValueError("Variavel SIDRA deve ser mensal sem ajuste.")
    periods = ",".join(pd.date_range(START, END, freq="MS").strftime("%Y%m"))
    url = (f"https://apisidra.ibge.gov.br/values/t/{table}/n1/1/v/{variable}"
           f"/p/{periods}/c{classification}/{category}?formato=json")
    response, url = fetch(url)
    if not isinstance(response, list) or not response:
        raise ValueError("Resposta SIDRA invalida.")
    records = response[1:]
    if any(r["D1C"] != "1" or r["D2C"] != str(variable) or r["D4C"] != str(category)
           or r["MN"] != var["unidade"] for r in records):
        raise ValueError("Territorio/variavel/categoria/unidade inesperados na resposta.")
    df = pd.DataFrame({"data_ref": [f'{r["D3C"][:4]}-{r["D3C"][4:]}-01' for r in records],
                       "valor": [r["V"] for r in records]})
    meta = {"nome": f"{label} - {category_meta['nome']}", "unidade": "indice (2022=100)",
            "tema": "atividade", "ajuste_sazonal": "nao", "fonte": "IBGE",
            "url": url, "metadata_url": metadata_url, "tabela": table, "variavel": variable,
            "classificacao": classification, "categoria": category, "territorio": "Brasil",
            "titulo_oficial": var["nome"], "categoria_oficial": category_meta["nome"]}
    return code, store(code, df, meta, response, official)


def download() -> dict:
    core.RAW.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(bcb, n, config) for n, config in SGS.items()]
        tasks += [pool.submit(sidra, code, config) for code, config in SIDRA.items()]
        results = dict(task.result() for task in tasks)
    (core.RAW / "catalog.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    # Independent official reference, not a ninth series in the demonstration database.
    url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados"
           "?formato=json&dataInicial=01/12/2022&dataFinal=31/12/2025")
    official, url = fetch(url)
    (core.RAW / "reference_ipca_13522.json").write_text(
        json.dumps({"url": url, "extraido_em": core.now(), "dados": official}, indent=2),
        encoding="utf-8")
    core.audit("download", "ok", series=list(results))
    return {"series": list(results), "janela": [START, END], "tipo": "dados_publicos_reais"}
