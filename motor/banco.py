"""Carrega, valida e consulta o banco de teses e o catalogo de pecas.

Estrutura em disco:
    banco/<area>/teses.json   lista de teses
    banco/<area>/pecas.json   dict peca_id -> especificacao da peca
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "banco"

AREAS = {
    "trabalhista_empresa": "Trabalhista - lado da EMPRESA (reclamada) [prioridade]",
    "trabalhista_empregado": "Trabalhista - lado do EMPREGADO (reclamante)",
    "civel": "Civel",
    "familia": "Familia e sucessoes",
}

TIPOS_TESE = {"preliminar", "prejudicial", "merito", "recursal", "inicial", "execucao"}
TIPOS_SECAO = {"texto", "campo", "fatos_autor", "fatos_reu", "teses", "pedidos", "fecho"}
CAMPOS_TESE = {"id", "titulo", "peca", "tipo", "tags", "texto", "fundamentos"}
PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_\.]+)\s*\}\}")


def _ler(caminho: Path):
    with caminho.open(encoding="utf-8") as f:
        return json.load(f)


def carregar_area(area: str) -> tuple[list[dict], dict]:
    if area not in AREAS:
        raise ValueError(f"Area desconhecida: {area}. Opcoes: {', '.join(AREAS)}")
    pasta = BANCO / area
    teses: list[dict] = []
    for arq in sorted(pasta.glob("teses*.json")):  # teses.json, teses_merito.json, ...
        teses += _ler(arq)
    pecas = _ler(pasta / "pecas.json")
    return teses, pecas


def validar_area(area: str) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia = banco consistente)."""
    erros: list[str] = []
    try:
        teses, pecas = carregar_area(area)
    except Exception as e:  # arquivo ausente ou JSON invalido
        return [f"[{area}] nao foi possivel carregar: {e}"]

    try:
        tags_validas = set(_ler(BANCO / area / "tags.json"))
    except Exception as e:
        return [f"[{area}] tags.json ausente ou invalido: {e}"]

    ids: set[str] = set()
    for t in teses:
        tid = t.get("id", "<sem id>")
        faltam = CAMPOS_TESE - set(t)
        if faltam:
            erros.append(f"[{area}] tese {tid}: campos ausentes {sorted(faltam)}")
        if tid in ids:
            erros.append(f"[{area}] id duplicado: {tid}")
        ids.add(tid)
        for tag in t.get("tags", []):
            if tag not in tags_validas:
                erros.append(f"[{area}] tese {tid}: tag fora de tags.json: {tag!r}")
        if t.get("tipo") not in TIPOS_TESE:
            erros.append(f"[{area}] tese {tid}: tipo invalido {t.get('tipo')!r}")
        for p in t.get("peca", []):
            if p not in pecas:
                erros.append(f"[{area}] tese {tid}: peca inexistente {p!r}")
        if not isinstance(t.get("fundamentos", []), list) or not t.get("fundamentos"):
            erros.append(f"[{area}] tese {tid}: 'fundamentos' deve ser lista nao vazia")
        if len(t.get("texto", "")) < 80:
            erros.append(f"[{area}] tese {tid}: texto muito curto")
    for t in teses:
        for outro in t.get("incompativel_com", []):
            if outro not in ids:
                erros.append(f"[{area}] tese {t['id']}: incompativel_com aponta id inexistente {outro!r}")

    for pid, p in pecas.items():
        for k in ("nome", "papel", "prazo", "secoes"):
            if k not in p:
                erros.append(f"[{area}] peca {pid}: campo ausente {k!r}")
        for s in p.get("secoes", []):
            if s.get("tipo") not in TIPOS_SECAO:
                erros.append(f"[{area}] peca {pid}: secao {s.get('id')!r} tipo invalido {s.get('tipo')!r}")
            if s.get("tipo") == "teses":
                tipos = s.get("filtro", {}).get("tipo", [])
                if not tipos or not set(tipos) <= TIPOS_TESE:
                    erros.append(f"[{area}] peca {pid}: secao {s.get('id')!r} filtro.tipo invalido")
    return erros


def validar_tudo() -> list[str]:
    erros: list[str] = []
    for area in AREAS:
        erros += validar_area(area)
    return erros


def _normalizar(txt: str) -> str:
    import unicodedata

    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


def selecionar_teses(area: str, peca: str, caso: dict) -> dict:
    """Escolhe as teses aplicaveis ao caso.

    Criterios (nesta ordem):
      1. `sempre: true`                      -> entra em toda peca em que esta listada
      2. tag da tese  x  caso["pedidos"]      -> entra (pedido/tema citado pelo usuario)
      3. id em caso["teses_forcadas"]         -> entra
      4. gatilho (palavra-chave) no texto     -> SUGERIDA (entra marcada, revisar)
    caso["teses_excluidas"] remove ids. Teses incompativeis entre si geram aviso.
    """
    teses, pecas = carregar_area(area)
    if peca not in pecas:
        raise ValueError(f"Peca {peca!r} nao existe em {area}. Opcoes: {', '.join(pecas)}")

    pedidos = {_normalizar(p) for p in caso.get("pedidos", [])}
    forcadas = set(caso.get("teses_forcadas", []))
    excluidas = set(caso.get("teses_excluidas", []))
    texto_caso = _normalizar(
        " ".join(str(caso.get(k, "")) for k in ("fatos_autor", "versao_reu", "resumo", "observacoes"))
    )

    escolhidas: list[dict] = []
    avisos: list[str] = []
    for t in teses:
        if peca not in t["peca"] or t["id"] in excluidas:
            continue
        motivo = None
        if t.get("sempre"):
            motivo = "padrao"
        elif pedidos & {_normalizar(x) for x in t["tags"]}:
            motivo = "pedido"
        elif t["id"] in forcadas:
            motivo = "forcada"
        else:
            hit = [g for g in t.get("gatilhos", []) if _normalizar(g) in texto_caso]
            if hit:
                motivo = "sugerida (gatilho: " + ", ".join(hit[:3]) + ")"
        if motivo:
            escolhidas.append({**t, "_motivo": motivo})

    escolhidas.sort(key=lambda t: (t.get("ordem", 500), t["id"]))
    ids = {t["id"] for t in escolhidas}
    for t in escolhidas:
        for outro in t.get("incompativel_com", []):
            if outro in ids:
                avisos.append(f"INCOMPATIVEIS: '{t['id']}' x '{outro}' - escolha uma linha de defesa.")
    return {"teses": escolhidas, "avisos": sorted(set(avisos)), "peca": pecas[peca]}


def preencher(texto: str, caso: dict) -> tuple[str, set[str]]:
    """Troca {{campo}} pelo valor do caso (aceita campo.subcampo). Devolve (texto, faltantes)."""
    faltantes: set[str] = set()

    def sub(m: re.Match) -> str:
        chave = m.group(1)
        valor = caso
        for parte in chave.split("."):
            if isinstance(valor, dict) and parte in valor and valor[parte] not in (None, ""):
                valor = valor[parte]
            else:
                faltantes.add(chave)
                return f"[{chave} ●]"
        return str(valor)

    return PLACEHOLDER.sub(sub, texto), faltantes
