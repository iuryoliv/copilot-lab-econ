from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from econlab import core


def accumulated(df: pd.DataFrame) -> pd.DataFrame:
    df = core.monthly(df, minimum=12)
    if (df.valor <= -100).any():
        raise ValueError("Taxa mensal deve ser maior que -100%.")
    df["valor"] = ((1 + df.valor / 100).rolling(12).apply(np.prod, raw=True) - 1) * 100
    return df.iloc[11:].reset_index(drop=True)


def quarter_pair(frames: dict[str, pd.DataFrame]) -> dict:
    checked = {code: core.monthly(df, minimum=6) for code, df in frames.items()}
    if not checked:
        raise ValueError("Selecione ao menos uma serie.")
    common = set.intersection(*(set(df.data_ref) for df in checked.values()))
    periods = pd.PeriodIndex(sorted(common), freq="M")
    full = sorted(q for q in set(periods.asfreq("Q")) if sum(periods.asfreq("Q") == q) == 3)
    pairs = [q for q in full if q - 1 in full]
    if not pairs:
        raise ValueError("Sem dois trimestres completos consecutivos no periodo comum.")
    latest = pairs[-1]
    previous = latest - 1
    months = pd.date_range(previous.start_time, latest.end_time, freq="MS").strftime("%Y-%m-%d").tolist()
    result = {}
    for code, df in checked.items():
        values = df.set_index("data_ref").loc[months, "valor"]
        before, after = float(values.iloc[:3].mean()), float(values.iloc[3:].mean())
        if before == 0:
            raise ValueError("Media anterior nula.")
        result[code] = {"media_anterior": before, "media_atual": after,
                        "variacao_percentual": 100 * (after / before - 1),
                        "valores": [float(x) for x in values]}
    return {"trimestre_anterior": str(previous), "trimestre_atual": str(latest),
            "meses": months, "series": result}


def seasonal(df: pd.DataFrame, adjustment: str, method: str = "STL") -> pd.DataFrame:
    if adjustment != "nao":
        raise ValueError("Nao reajustar serie ja ajustada ou sem metadado confirmado.")
    if method != "STL":
        raise ValueError("Somente STL disponivel; X-13 nao instalado, sem substituicao silenciosa.")
    result = core.monthly(df, minimum=36)
    fit = STL(result.valor.to_numpy(), period=12, robust=True).fit()
    result["valor"] = result.valor - fit.seasonal
    return result


def save_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False),
                    encoding="utf-8")


def save_manifest(folder: Path, result: dict, files: list[str]) -> dict:
    result["artefatos"] = {name: core.digest(folder / name) for name in files}
    save_json(folder / "manifest.json", result)
    core.audit("analytics", "ok", pasta=str(folder), artefatos=files)
    return result


def inflation() -> dict:
    folder = core.OUT / "inflacao"
    folder.mkdir(parents=True, exist_ok=True)
    frames, metadata = {}, {}
    for code in ("BCB_433", "BCB_189"):
        df, meta = core.series(code)
        if meta["unidade"] != "% a.m." or meta["ajuste_sazonal"] != "nao":
            raise ValueError("Acumulado requer taxas mensais percentuais sem ajuste.")
        frames[code] = accumulated(df).set_index("data_ref").valor
        metadata[code] = meta
    table = pd.DataFrame(frames).dropna().tail(36)
    if len(table) != 36:
        raise ValueError("Historico insuficiente para 36 pontos comuns de acumulado.")
    table.to_csv(folder / "tabela.csv", float_format="%.10f")
    with plt.rc_context({"font.size": 10}):
        fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
        for code, label in (("BCB_433", "IPCA"), ("BCB_189", "IGP-M")):
            ax.plot(pd.to_datetime(table.index), table[code], label=label, linewidth=2)
        ax.axhline(0, color="gray", linewidth=0.6)
        ax.set(title="IPCA e IGP-M: acumulado composto em 12 meses", ylabel="% em 12 meses")
        ax.legend()
        extracted = max(m["extraido_em"] for m in metadata.values())
        fig.supxlabel(f"Fonte: BCB/SGS 433 e 189 | Extracao UTC: {extracted[:19]}", fontsize=8)
        fig.savefig(folder / "grafico.png", dpi=150)
        plt.close(fig)
    result = {"tipo": "inflacao", "metodo": "100 * (produto(1+taxa_mensal/100)-1)",
              "pontos": len(table), "inicio": table.index[0], "fim": table.index[-1],
              "ultimo": {code: float(table[code].iloc[-1]) for code in table.columns},
              "unidade": "% em 12 meses", "fontes": metadata, "gerado_em": core.now()}
    return save_manifest(folder, result, ["tabela.csv", "grafico.png"])


def activity(method: str = "STL") -> dict:
    pmc, pmc_meta = core.series("IBGE_PMC")
    ibc, ibc_meta = core.series("BCB_24364")
    if ibc_meta["ajuste_sazonal"] != "sim":
        raise ValueError("IBC-Br deve possuir ajuste oficial confirmado.")
    adjusted = seasonal(pmc, pmc_meta["ajuste_sazonal"], method)
    pair = quarter_pair({"PMC_STL": adjusted, "BCB_24364": ibc})
    folder = core.OUT / "atividade"
    folder.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(folder / "pmc_stl.csv", index=False, float_format="%.10f")
    table = pd.DataFrame({"data_ref": pair["meses"],
                          **{k: v["valores"] for k, v in pair["series"].items()}})
    table.to_csv(folder / "trimestres.csv", index=False, float_format="%.10f")
    result = {"tipo": "atividade", **pair, "metodo_pmc": "STL aditivo, robust=True, period=12",
              "metodo_ibc": "Ajuste sazonal oficial BCB; nao reajustado",
              "limitacoes": "STL ilustrativo, nao equivale ao X-13 nem ao ajuste oficial IBGE. "
                            "Estimativas de ponta e revisoes dependem da amostra 2022-2025. "
                            "Indices com bases distintas: comparar variacoes, nao niveis.",
              "fontes": {"IBGE_PMC": pmc_meta, "BCB_24364": ibc_meta},
              "gerado_em": core.now()}
    return save_manifest(folder, result, ["pmc_stl.csv", "trimestres.csv"])


def validated_manifest(kind: str) -> dict:
    if kind not in ("inflacao", "atividade"):
        raise ValueError("Resultado desconhecido.")
    folder = core.OUT / kind
    result = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    expected = {"inflacao": {"tabela.csv", "grafico.png"},
                "atividade": {"pmc_stl.csv", "trimestres.csv"}}[kind]
    if set(result["artefatos"]) != expected:
        raise ValueError("Lista de artefatos divergente.")
    for name, sha in result["artefatos"].items():
        if core.digest(folder / name) != sha:
            raise ValueError(f"Artefato alterado: {kind}/{name}")
    for code, meta in result["fontes"].items():
        _, current = core.series(code)
        if current["sha256"] != meta["sha256"]:
            raise ValueError("Resultado desatualizado em relacao a base.")
    if kind == "inflacao":
        table = pd.read_csv(folder / "tabela.csv")
        if len(table) != result["pontos"] or table.data_ref.iloc[-1] != result["fim"]:
            raise ValueError("Tabela e manifesto divergentes.")
        for code in result["ultimo"]:
            if abs(float(table[code].iloc[-1]) - result["ultimo"][code]) > 1e-8:
                raise ValueError("Numeros da tabela e manifesto divergentes.")
    else:
        table = pd.read_csv(folder / "trimestres.csv")
        if list(table.data_ref) != result["meses"]:
            raise ValueError("Meses da tabela e manifesto divergentes.")
        for code, values in result["series"].items():
            rate = 100 * (table[code].iloc[3:].mean() / table[code].iloc[:3].mean() - 1)
            if abs(rate - values["variacao_percentual"]) > 1e-8:
                raise ValueError("Taxas da tabela e manifesto divergentes.")
    return result
