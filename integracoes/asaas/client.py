"""Esqueleto de integracao com o Asaas (API v3).

Preencha ASAAS_API_KEY no .env (NUNCA no codigo). Comece pelo sandbox.
Docs: https://docs.asaas.com
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[2]
URLS = {
    "sandbox": "https://api-sandbox.asaas.com/v3",
    "producao": "https://api.asaas.com/v3",
}


class AsaasError(Exception):
    def __init__(self, status: int, corpo):
        super().__init__(f"Asaas HTTP {status}: {corpo}")
        self.status, self.corpo = status, corpo


def _env(nome: str, padrao: str | None = None) -> str | None:
    if os.environ.get(nome):
        return os.environ[nome]
    arq = RAIZ / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.startswith(nome + "="):
                return linha.split("=", 1)[1].strip().strip('"')
    return padrao


class AsaasClient:
    def __init__(self, api_key: str | None = None, ambiente: str | None = None):
        self.api_key = api_key or _env("ASAAS_API_KEY")
        if not self.api_key:
            raise RuntimeError("ASAAS_API_KEY ausente (.env ou variavel de ambiente).")
        self.base = URLS[ambiente or _env("ASAAS_AMBIENTE", "sandbox")]
        self.s = requests.Session()
        self.s.headers.update({
            "access_token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "motor-pecas-integracao-asaas",  # o Asaas exige User-Agent
        })

    def _req(self, metodo: str, caminho: str, **kw):
        for tentativa in range(3):
            r = self.s.request(metodo, self.base + caminho, timeout=30, **kw)
            if r.status_code == 429:  # limite de requisicoes
                time.sleep(2 ** tentativa)
                continue
            break
        try:
            corpo = r.json()
        except ValueError:
            corpo = r.text
        if not r.ok:
            raise AsaasError(r.status_code, corpo)
        return corpo

    # ---- clientes
    def criar_cliente(self, nome: str, cpf_cnpj: str, email: str | None = None, celular: str | None = None, **extra):
        return self._req("POST", "/customers", json={"name": nome, "cpfCnpj": cpf_cnpj, "email": email,
                                                       "mobilePhone": celular, **extra})

    def buscar_cliente_por_cpf(self, cpf_cnpj: str):
        return self._req("GET", "/customers", params={"cpfCnpj": cpf_cnpj}).get("data", [])

    # ---- cobrancas
    def criar_cobranca(self, cliente_id: str, valor: float, vencimento: str, forma: str = "UNDEFINED",
                       descricao: str = "", referencia: str | None = None, **extra):
        """forma: BOLETO | PIX | CREDIT_CARD | UNDEFINED. vencimento: AAAA-MM-DD."""
        return self._req("POST", "/payments", json={
            "customer": cliente_id, "billingType": forma, "value": valor, "dueDate": vencimento,
            "description": descricao, "externalReference": referencia, **extra})

    def consultar_cobranca(self, pagamento_id: str):
        return self._req("GET", f"/payments/{pagamento_id}")

    def listar_cobrancas(self, **filtros):
        return self._req("GET", "/payments", params=filtros)

    def qrcode_pix(self, pagamento_id: str):
        return self._req("GET", f"/payments/{pagamento_id}/pixQrCode")

    def cancelar_cobranca(self, pagamento_id: str):
        return self._req("DELETE", f"/payments/{pagamento_id}")

    # ---- assinaturas (recorrencia)
    def criar_assinatura(self, cliente_id: str, valor: float, proximo_vencimento: str, ciclo: str = "MONTHLY",
                         forma: str = "UNDEFINED", descricao: str = "", **extra):
        return self._req("POST", "/subscriptions", json={
            "customer": cliente_id, "billingType": forma, "value": valor, "nextDueDate": proximo_vencimento,
            "cycle": ciclo, "description": descricao, **extra})
