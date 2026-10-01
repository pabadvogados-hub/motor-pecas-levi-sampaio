"""Redacao assistida por IA (opcional): o Claude refina a minuta do motor.

O motor entrega ao modelo a estrutura, as teses escolhidas (com fundamentos) e os fatos.
O modelo NAO pode acrescentar citacao que nao esteja nas teses; qualquer citacao nova deve
vir marcada [CONFERIR]. Sem ANTHROPIC_API_KEY o comando avisa e nada e enviado.
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

SISTEMA = """Voce e um(a) advogado(a) brasileiro(a) senior redigindo peca processual a partir de uma MINUTA do motor do escritorio.

REGRAS INEGOCIAVEIS
1. Use somente as normas, sumulas e temas listados em FUNDAMENTOS/JURISPRUDENCIA das teses fornecidas. Se julgar necessario citar algo a mais, escreva a citacao seguida de [CONFERIR] - nunca afirme numero de sumula, tema, artigo, ementa ou processo de memoria como certo.
2. Nunca invente fatos, datas, valores, nomes, documentos. Dado ausente permanece como [... ●] (lacuna), exatamente nesse formato.
3. Preserve a estrutura de secoes e titulos da minuta. Adapte cada tese aos FATOS do caso: troque o generico pelo concreto, impugne especificamente o que a inicial/peticao alega (art. 341 CPC), corte o que nao se aplica ao caso.
4. Portugues juridico formal, impessoal, claro, sem travessao longo, sem emoji, sem floreio. Paragrafos curtos. Nada de "data venia" em excesso.
5. Teses marcadas [REVISAR: sugerida...] so permanecem se os fatos sustentam; caso contrario, remova e diga no fim, em uma linha, "Removida: <tese> (motivo)".
6. Teses incompativeis devem ser coordenadas como defesa subsidiaria ("por cautela, caso superado...") ou escolhidas conforme os fatos. Nunca se contradiga.
7. Saida: markdown simples. '# ' enderecamento, '## ' titulo de secao, '### ' subtitulo, '> ' citacao longa, 'a) ' itens de pedido. Sem comentarios fora da peca, exceto a ultima secao '## NOTAS PARA O ADVOGADO' (fora da peca) com: lacunas pendentes, riscos e pontos a conferir.
"""


def _chave() -> str | None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("ANTHROPIC_API_KEY="):
                return linha.split("=", 1)[1].strip().strip('"')
    return None


def montar_prompt(m: dict) -> str:
    caso = {k: v for k, v in m["caso"].items() if not k.startswith("_")}
    partes = [f"PECA: {m['peca']['nome']}", f"PRAZO/OBSERVACAO: {m['peca']['prazo']}", "",
              "DADOS DO CASO (json):", __import__("json").dumps(caso, ensure_ascii=False, indent=2), "",
              "TESES SELECIONADAS (fundamentos autorizados):"]
    for t in m["teses"]:
        partes.append(f"- {t['titulo']} [{t['tipo']}; {t['_motivo']}]\n  fundamentos: {'; '.join(t['fundamentos'])}"
                      f"\n  jurisprudencia: {'; '.join(t.get('jurisprudencia', [])) or '-'}")
    if m["avisos"]:
        partes += ["", "AVISOS: " + " | ".join(m["avisos"])]
    partes += ["", "MINUTA DO MOTOR (reescreva e adapte aos fatos):", ""]
    for b in m["blocos"]:
        pref = {"endereco": "# ", "titulo": "## ", "subtitulo": "### ", "citacao": "> "}.get(b["k"], "")
        partes.append(pref + b["t"])
    return "\n".join(partes)


def redigir(m: dict, modelo: str, max_tokens: int = 16000) -> str:
    chave = _chave()
    if not chave:
        raise RuntimeError("ANTHROPIC_API_KEY ausente (variavel de ambiente ou arquivo .env na raiz do projeto).")
    import anthropic

    cliente = anthropic.Anthropic(api_key=chave)
    resp = cliente.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        system=SISTEMA,
        messages=[{"role": "user", "content": montar_prompt(m)}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
