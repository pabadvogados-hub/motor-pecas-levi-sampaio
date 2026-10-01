"""Dados do escritorio e formatacao das pecas. EDITE ESTE ARQUIVO.

Tudo que estiver como None ou "[●]" aparece destacado na minuta para voce completar.
Nada aqui e inventado: preencha com os dados reais.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

ESCRITORIO = {
    "nome": "Braga & Braz Advogados",
    "cidade": "[cidade ●]",
    "advogados": [
        # {"nome": "Renato Braz", "oab": "OAB/UF 00.000"},
        {"nome": "[advogado ●]", "oab": "[OAB/UF ●]"},
    ],
    "endereco": "[endereco do escritorio ●]",
    "email": "[e-mail ●]",
    "telefone": "[telefone ●]",
}

# Formatacao padrao (ajuste ao padrao do escritorio)
FORMATO = {
    "fonte": "Times New Roman",
    "tamanho_corpo": 12,
    "espacamento": 1.5,
    "recuo_primeira_linha_cm": 2.5,
    "margens_cm": {"topo": 3.0, "base": 2.0, "esquerda": 3.0, "direita": 2.0},
    "alinhamento": "justificado",
}

# Papel timbrado (.docx) opcional. Se existir, a peca e gerada sobre ele
# (cabecalho/rodape/margens do timbrado preservados).
TIMBRADO = Path(os.environ.get("MOTOR_TIMBRADO", RAIZ / "config" / "TIMBRADO.docx"))

# Modelo usado na redacao assistida (comando `redigir`).
# A chave vem de ANTHROPIC_API_KEY (variavel de ambiente ou arquivo .env na raiz).
MODELO_IA = os.environ.get("MOTOR_MODELO", "claude-opus-5-5")
