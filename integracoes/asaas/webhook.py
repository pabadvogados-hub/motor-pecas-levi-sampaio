"""Receptor de webhooks do Asaas (FastAPI opcional: pip install fastapi uvicorn).

No painel do Asaas, cadastre a URL e um token de autenticacao; coloque o mesmo
em ASAAS_WEBHOOK_TOKEN. O Asaas envia esse token no header `asaas-access-token`.
Rode:  uvicorn integracoes.asaas.webhook:app --port 8020
"""
import hmac

from fastapi import FastAPI, Header, HTTPException, Request

from .client import _env

app = FastAPI()

# Eventos mais usados: PAYMENT_CREATED, PAYMENT_CONFIRMED, PAYMENT_RECEIVED,
# PAYMENT_OVERDUE, PAYMENT_DELETED, PAYMENT_REFUNDED.
def tratar_evento(evento: str, pagamento: dict) -> None:
    """TODO: ligue ao seu fluxo (ex.: marcar honorario como pago, avisar o cliente)."""
    print(evento, pagamento.get("id"), pagamento.get("externalReference"))


@app.post("/asaas/webhook")
async def receber(req: Request, asaas_access_token: str | None = Header(default=None)):
    esperado = _env("ASAAS_WEBHOOK_TOKEN")
    if not esperado or not hmac.compare_digest(asaas_access_token or "", esperado):
        raise HTTPException(401, "token invalido")
    dados = await req.json()
    tratar_evento(dados.get("event", ""), dados.get("payment", {}))
    return {"ok": True}  # responda 200 rapido; o Asaas reenvia em caso de falha
