"""Linha de comando do motor.

    python -m motor areas
    python -m motor pecas trabalhista_empresa
    python -m motor tags trabalhista_empresa
    python -m motor novo trabalhista_empresa contestacao -o saida/caso.json
    python -m motor gerar saida/caso.json            # minuta .docx + relatorio de conferencia
    python -m motor redigir saida/caso.json          # igual, refinada pelo Claude (precisa de chave)
    python -m motor validar                          # confere o banco
    python -m motor prazo 30/09/2026 recurso_ordinario
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from . import banco, docx_fmt, montar, prazos

RAIZ = banco.RAIZ


def _config():
    sys.path.insert(0, str(RAIZ))
    from config import escritorio

    return escritorio


def cmd_areas(_):
    for k, v in banco.AREAS.items():
        t, p = banco.carregar_area(k)
        print(f"{k:24} {len(t):3} teses  {len(p):2} pecas   {v}")


def cmd_pecas(a):
    _, pecas = banco.carregar_area(a.area)
    for pid, p in pecas.items():
        print(f"{pid:32} {p['nome']}  [{p['papel']}]  prazo: {p['prazo']}")


def cmd_tags(a):
    tags = json.loads((banco.BANCO / a.area / "tags.json").read_text(encoding="utf-8"))
    for k, v in tags.items():
        print(f"{k:34} {v}")


def cmd_novo(a):
    _, pecas = banco.carregar_area(a.area)
    if a.peca not in pecas:
        sys.exit(f"Peca invalida. Opcoes: {', '.join(pecas)}")
    p = pecas[a.peca]
    modelo = {
        "area": a.area, "peca": a.peca,
        "processo": "", "vara": "", "cidade": "",
        "autor": {"nome": "", "qualificacao": ""},
        "reu": {"nome": "", "qualificacao": ""},
        "data_admissao": "", "data_demissao": "", "funcao": "", "ultimo_salario": "",
        "fatos_autor": "Resumo do que a parte contraria alega (um paragrafo por bloco, separados por linha em branco).",
        "versao_reu": "Nossa versao dos fatos (so o que o cliente confirmou e pode provar).",
        "pedidos": [],
        "teses_forcadas": [], "teses_excluidas": [],
        "observacoes": "",
        "_ajuda": {"campos_obrigatorios": p.get("campos_obrigatorios", []),
                   "dica": f"Veja as tags com: python -m motor tags {a.area}"},
    }
    destino = Path(a.o)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(modelo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Caso-modelo criado: {destino}\nPreencha e rode: python -m motor gerar {destino}")


def _carregar_caso(caminho: str) -> dict:
    caso = json.loads(Path(caminho).read_text(encoding="utf-8"))
    caso.pop("_ajuda", None)
    return caso


def _nome_base(caso: dict) -> str:
    base = caso.get("autor", {}).get("nome") or caso.get("reu", {}).get("nome") or "caso"
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_") or "caso"
    return f"{base}_{caso['peca']}_{datetime.now():%Y%m%d_%H%M}"


def _gerar(a, com_ia: bool):
    cfg = _config()
    caso = _carregar_caso(a.caso)
    m = montar.montar(caso, cfg.ESCRITORIO)
    saida = Path(a.saida)
    base = _nome_base(caso)
    blocos = m["blocos"]
    if com_ia:
        from . import redigir

        texto = redigir.redigir(m, a.modelo or cfg.MODELO_IA)
        corpo, _, notas = texto.partition("## NOTAS PARA O ADVOGADO")
        blocos = docx_fmt.blocos_de_markdown(corpo)
        (saida / f"{base}_notas_ia.md").parent.mkdir(parents=True, exist_ok=True)
        (saida / f"{base}_notas_ia.md").write_text("## NOTAS PARA O ADVOGADO" + notas, encoding="utf-8")
    docx = docx_fmt.gerar(blocos, saida / f"{base}.docx", cfg.FORMATO, cfg.TIMBRADO)
    rel = saida / f"{base}_conferencia.md"
    rel.write_text(montar.relatorio(m), encoding="utf-8")
    print(f"Peca:      {docx}\nConferir:  {rel}")
    if m["faltantes"]:
        print(f"Atencao: {len(m['faltantes'])} dado(s) faltando (amarelo no .docx): {', '.join(m['faltantes'])}")
    for aviso in m["avisos"]:
        print("Aviso:", aviso)


def cmd_gerar(a):
    _gerar(a, False)


def cmd_redigir(a):
    try:
        _gerar(a, True)
    except RuntimeError as e:
        sys.exit(f"Erro: {e}")


def cmd_validar(_):
    erros = banco.validar_tudo()
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    print("Banco consistente.")


def cmd_prazo(a):
    inicio = datetime.strptime(a.data, "%d/%m/%Y").date()
    if a.dias:
        dias = a.dias
    else:
        ramo = prazos.PRAZOS_COMUNS["trabalhista" if a.regime == "clt" else "civel"]
        dias = ramo.get(a.tipo)
        if dias is None:
            sys.exit(f"Tipo desconhecido; use --dias N. Conhecidos: "
                     f"{sorted(ramo)} (regime {a.regime})")
    fim = prazos.calcular(inicio, dias, a.regime)
    print(f"{dias} dias uteis ({a.regime.upper()}) a partir de {inicio:%d/%m/%Y}: vence em "
          f"{fim:%d/%m/%Y} ({['seg','ter','qua','qui','sex','sab','dom'][fim.weekday()]}).")
    print("CONFIRA feriados locais, portarias do tribunal e a data real da ciencia/publicacao.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="motor", description="Motor de pecas - trabalhista, civel e familia")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("areas").set_defaults(f=cmd_areas)
    for nome, f in (("pecas", cmd_pecas), ("tags", cmd_tags)):
        s = sp.add_parser(nome)
        s.add_argument("area", choices=banco.AREAS)
        s.set_defaults(f=f)
    s = sp.add_parser("novo")
    s.add_argument("area", choices=banco.AREAS)
    s.add_argument("peca")
    s.add_argument("-o", default="saida/caso.json")
    s.set_defaults(f=cmd_novo)
    for nome, f in (("gerar", cmd_gerar), ("redigir", cmd_redigir)):
        s = sp.add_parser(nome)
        s.add_argument("caso")
        s.add_argument("--saida", default=str(RAIZ / "saida"))
        s.add_argument("--modelo")
        s.set_defaults(f=f)
    sp.add_parser("validar").set_defaults(f=cmd_validar)
    s = sp.add_parser("prazo")
    s.add_argument("data", help="dia da ciencia/publicacao, DD/MM/AAAA")
    s.add_argument("tipo", nargs="?", default="")
    s.add_argument("--dias", type=int)
    s.add_argument("--regime", choices=["clt", "cpc"], default="clt")
    s.set_defaults(f=cmd_prazo)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
