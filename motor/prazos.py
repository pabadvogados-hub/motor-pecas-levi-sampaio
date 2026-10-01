"""Calculadora de prazos em dias uteis (art. 775 CLT / art. 219 CPC).

Considera: sabados e domingos, feriados nacionais fixos, Carnaval (segunda e terca),
Sexta-feira Santa e Corpus Christi (pontos facultativos que os tribunais costumam
tratar como nao uteis) e suspensao de fim de ano.
NAO conhece feriados estaduais/municipais nem portarias locais: CONFIRA no calendario do tribunal.
"""
from __future__ import annotations

from datetime import date, timedelta

FIXOS = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)]

PRAZOS_COMUNS = {
    "trabalhista": {
        "recurso_ordinario": 8, "contrarrazoes": 8, "embargos_declaracao": 5,
        "agravo_peticao": 8, "embargos_execucao": 5, "impugnacao_calculos": 8,
        "recurso_revista": 8, "agravo_instrumento": 8, "excecao_incompetencia": 5,
        "manifestacao_laudo": 5,
    },
    "civel": {
        "contestacao": 15, "replica": 15, "apelacao": 15, "contrarrazoes": 15,
        "agravo_instrumento": 15, "embargos_declaracao": 5, "impugnacao_cumprimento": 15,
        "embargos_execucao": 15, "pagamento_cumprimento": 15,
    },
}


def pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


def nao_uteis(ano: int) -> set[date]:
    p = pascoa(ano)
    s = {date(ano, m, d) for m, d in FIXOS}
    s |= {p - timedelta(days=48), p - timedelta(days=47), p - timedelta(days=2), p + timedelta(days=60)}
    return s


def suspenso(d: date, regime: str) -> bool:
    if regime == "clt":  # Lei 5.010/66, art. 62, I: 20/12 a 6/1 na Justica do Trabalho
        return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 6)
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)  # CPC art. 220


def util(d: date, regime: str, extras: set[date]) -> bool:
    return d.weekday() < 5 and d not in nao_uteis(d.year) and d not in extras and not suspenso(d, regime)


def calcular(inicio: date, dias: int, regime: str = "clt", extras: set[date] | None = None) -> date:
    """`inicio` = dia da ciencia/publicacao (exclui-se o dia do comeco, inclui-se o do vencimento)."""
    extras = extras or set()
    d, contados = inicio, 0
    while contados < dias:
        d += timedelta(days=1)
        if util(d, regime, extras):
            contados += 1
    return d
