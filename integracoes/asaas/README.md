# Integracao Asaas (esqueleto)

1. `pip install -r requirements.txt` (requests; fastapi/uvicorn so para o webhook)
2. No `.env` da raiz (nunca no git):
```
ASAAS_API_KEY=...            # painel Asaas > Integracoes
ASAAS_AMBIENTE=sandbox       # troque para producao so depois de testar
ASAAS_WEBHOOK_TOKEN=...      # segredo escolhido por voce
```
3. Uso:
```python
from integracoes.asaas import AsaasClient
a = AsaasClient()
c = a.criar_cliente("Fulano", "12345678909", email="f@x.com")
p = a.criar_cobranca(c["id"], 1500.00, "2026-11-10", forma="PIX", descricao="Honorarios", referencia="CASO-001")
print(p["invoiceUrl"])
```
4. Webhook: `webhook.py` (valida o token e chama `tratar_evento`, onde entra a sua regra).
5. Ideia de encaixe: ao gerar o contrato de honorarios, criar a cobranca/assinatura e gravar o id no caso.

Limites e campos: confira em https://docs.asaas.com (a API evolui).
