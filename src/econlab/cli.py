from __future__ import annotations

import argparse
import json
import sys

from econlab import core


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratorio local; sem publicacao ou cloud.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("download", help="Baixa somente BCB/IBGE, janela historica 2022-2025.")
    sub.add_parser("reset", help="Substitui somente data/econ_lab.db; preserva cache, outputs e logs.")
    proposal = sub.add_parser("proposal")
    proposal.add_argument("codigo", default="IBGE_PIMPF", nargs="?")
    auth = sub.add_parser("authorize", help="Etapa externa ao MCP; exige confirmacao no terminal.")
    auth.add_argument("codigo")
    auth.add_argument("proposta")
    auth.add_argument("--actor", required=True)
    args = parser.parse_args()
    if args.command == "download":
        from econlab.sources import download
        result = download()
    elif args.command == "reset":
        result = core.reset()
    elif args.command == "proposal":
        result = core.proposal(args.codigo)
    else:
        proposal = core.proposal(args.codigo)
        print(json.dumps(proposal, ensure_ascii=False, indent=2))
        phrase = f"AUTORIZAR {args.proposta}"
        if not sys.stdin.isatty():
            raise PermissionError("Autorizacao humana exige terminal interativo; sem pipe automatizado.")
        if input(f"Para autorizar esta carga por 10 minutos, digite {phrase}: ") != phrase:
            raise PermissionError("Carga nao autorizada.")
        result = core.approve(args.codigo, args.proposta, args.actor)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
