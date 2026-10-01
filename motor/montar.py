"""Monta a minuta: estrutura da peca + teses selecionadas + dados do caso.

Resultado: um modelo neutro (lista de blocos) que o docx_fmt transforma em .docx
e que o redigir.py pode entregar ao Claude para refinar.
"""
from __future__ import annotations

import re
from datetime import date

from . import banco

MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
ROMANO = re.compile(r"^([IVXL]+)\s*[-–.]")


def _blocos_texto(texto: str, caso: dict, faltantes: set, k: str = "p") -> list[dict]:
    texto, falt = banco.preencher(texto, caso)
    faltantes |= falt
    return [{"k": k, "t": par.strip()} for par in texto.split("\n\n") if par.strip()]


def _data_extenso(caso: dict) -> str:
    hoje = date.today()
    cidade = caso.get("cidade") or caso.get("_escritorio", {}).get("cidade", "[cidade ●]")
    return f"{cidade}, {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}."


def montar(caso: dict, escritorio: dict | None = None) -> dict:
    area, peca_id = caso["area"], caso["peca"]
    caso = {**caso, "_escritorio": escritorio or {}}
    sel = banco.selecionar_teses(area, peca_id, caso)
    peca = sel["peca"]

    faltantes: set[str] = set()
    blocos: list[dict] = []
    usadas: list[dict] = []
    vistos: set[str] = set()

    blocos += _blocos_texto(peca["enderecamento"], caso, faltantes, "endereco")
    if caso.get("processo"):
        blocos.append({"k": "processo", "t": f"Processo n. {caso['processo']}"})
    else:
        faltantes.add("processo")
        blocos.append({"k": "processo", "t": "Processo n. [numero ●]"})

    for sec in peca["secoes"]:
        tipo = sec["tipo"]
        if sec.get("titulo"):
            blocos.append({"k": "titulo", "t": sec["titulo"]})
        if tipo == "texto":
            blocos += _blocos_texto(sec["texto"], caso, faltantes)
        elif tipo == "campo":
            campo = sec["campo"]
            if caso.get(campo):
                blocos += _blocos_texto(caso[campo], caso, faltantes)
            else:
                faltantes.add(campo)
                blocos.append({"k": "p", "t": f"[{campo} ●]"})
        elif tipo in ("fatos_autor", "fatos_reu"):
            campo = "fatos_autor" if tipo == "fatos_autor" else "versao_reu"
            if caso.get(campo):
                blocos += _blocos_texto(caso[campo], caso, faltantes)
            else:
                faltantes.add(campo)
                blocos.append({"k": "p", "t": f"[{campo} ●]"})
        elif tipo == "teses":
            tipos = set(sec["filtro"]["tipo"])
            m = ROMANO.match(sec.get("titulo") or "")
            prefixo = m.group(1) if m else ""
            n = 0
            for t in sel["teses"]:
                if t["tipo"] not in tipos or t["id"] in vistos:
                    continue
                vistos.add(t["id"])
                usadas.append(t)
                n += 1
                num = f"{prefixo}.{n} " if prefixo else f"{n}. "
                blocos.append({"k": "subtitulo", "t": f"{num}{t['titulo']}"})
                if t["_motivo"].startswith("sugerida"):
                    blocos.append({"k": "nota", "t": f"[REVISAR: tese {t['_motivo']}. Apague se nao se aplica ao caso.]"})
                blocos += _blocos_texto(t["texto"], caso, faltantes)
            if n == 0:
                blocos.append({"k": "nota", "t": "[Nenhuma tese selecionada para esta secao. Veja o relatorio.]"})
        elif tipo == "pedidos":
            itens = [t["pedido_defesa"] for t in usadas if t.get("pedido_defesa")]
            itens += sec.get("fixos", [])
            blocos.append({"k": "p", "t": sec.get("intro", "Ante o exposto, requer:")})
            for i, it in enumerate(itens):
                letra = chr(ord("a") + i) if i < 26 else str(i + 1)
                texto, falt = banco.preencher(it, caso)
                faltantes |= falt
                blocos.append({"k": "item", "t": f"{letra}) {texto.rstrip(';.')}{'.' if i == len(itens) - 1 else ';'}"})
        elif tipo == "fecho":
            blocos.append({"k": "p", "t": sec.get("texto", "Nestes termos, pede deferimento.")})
            blocos.append({"k": "centro", "t": _data_extenso(caso)})
            for adv in (escritorio or {}).get("advogados", []):
                blocos.append({"k": "centro", "t": f"{adv['nome']}\n{adv['oab']}"})

    for campo in peca.get("campos_obrigatorios", []):
        valor = caso
        for parte in campo.split("."):
            valor = valor.get(parte) if isinstance(valor, dict) else None
        if valor in (None, ""):
            faltantes.add(campo)

    return {
        "caso": caso,
        "peca": peca,
        "blocos": blocos,
        "teses": usadas,
        "avisos": sel["avisos"],
        "faltantes": sorted(faltantes),
    }


def relatorio(m: dict) -> str:
    """Relatorio de conferencia em Markdown: tudo que o advogado deve checar antes de protocolar."""
    peca, caso = m["peca"], m["caso"]
    L = [f"# Relatorio de conferencia - {peca['nome']}", "",
         f"Area: {caso['area']}  |  Processo: {caso.get('processo') or '[●]'}", "",
         "> A minuta e um ponto de partida. Toda citacao abaixo deve ser conferida em fonte oficial "
         "antes do protocolo. O advogado responde pela peca.", ""]
    L += ["## Prazo", peca["prazo"], ""]
    if m["avisos"]:
        L += ["## Avisos"] + [f"- {a}" for a in m["avisos"]] + [""]
    if m["faltantes"]:
        L += ["## Dados faltando (aparecem como [... ●] na minuta)"] + [f"- {f}" for f in m["faltantes"]] + [""]
    L += ["## Teses usadas", "", "| tese | tipo | por que entrou |", "|---|---|---|"]
    L += [f"| {t['titulo']} | {t['tipo']} | {t['_motivo']} |" for t in m["teses"]] + [""]
    docs = list(peca.get("documentos", []))
    for t in m["teses"]:
        docs += t.get("prova", [])
    if docs:
        L += ["## Documentos e provas a reunir"] + [f"- {d}" for d in dict.fromkeys(docs)] + [""]
    if peca.get("alertas"):
        L += ["## Alertas da peca"] + [f"- {a}" for a in peca["alertas"]] + [""]
    riscos = [(t["titulo"], t["riscos"]) for t in m["teses"] if t.get("riscos")]
    if riscos:
        L += ["## Riscos por tese"] + [f"- **{a}**: {b}" for a, b in riscos] + [""]
    L += ["## Citacoes para CONFERIR (norma vigente, texto, numero)"]
    for t in m["teses"]:
        cit = t.get("fundamentos", []) + t.get("jurisprudencia", [])
        L.append(f"- **{t['titulo']}**: " + "; ".join(cit))
        for c in t.get("conferir", []):
            L.append(f"    - CONFERIR: {c}")
    return "\n".join(L) + "\n"
