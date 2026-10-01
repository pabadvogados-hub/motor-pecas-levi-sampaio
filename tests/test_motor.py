"""Testes de fumaca: banco consistente, toda peca monta e gera .docx, prazos corretos.

Rode:  python -m unittest discover -s tests -v
"""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import escritorio  # noqa: E402
from motor import banco, docx_fmt, montar, prazos  # noqa: E402


def caso_completo(area, peca, todas_tags=True):
    tags = list(json.loads((banco.BANCO / area / "tags.json").read_text(encoding="utf-8")))
    return {
        "area": area, "peca": peca, "processo": "0000000-00.2026.5.02.0000", "vara": "1a Vara",
        "orgao_julgador": "TRT", "foro_correto": "Comarca X", "cidade": "Sao Paulo",
        "autor": {"nome": "FULANO DE TAL", "qualificacao": "brasileiro"},
        "reu": {"nome": "EMPRESA LTDA", "qualificacao": "pessoa juridica"},
        "data_admissao": "01/02/2020", "data_demissao": "10/03/2025", "data_ajuizamento": "01/06/2025",
        "funcao": "auxiliar", "ultimo_salario": "R$ 2.000,00", "jornada_contratual": "44h semanais",
        "fatos_autor": "A parte alega horas extras e dano moral.\n\nPede vinculo.",
        "versao_reu": "Contrato regular.", "decisao_recorrida": "Sentenca procedente em parte.",
        "divergencias_calculo": "Item A.", "garantia_juizo": "Deposito.", "pontos_laudo": "Ponto 1.",
        "resultado_instrucao": "Testemunha confirmou.", "condicoes_acordo": "R$ 10.000,00.",
        "pedidos": tags if todas_tags else [],
    }


class TestBanco(unittest.TestCase):
    def test_banco_valido(self):
        self.assertEqual(banco.validar_tudo(), [])

    def test_trabalhista_empresa_tem_pecas_prioritarias(self):
        _, pecas = banco.carregar_area("trabalhista_empresa")
        for p in ("contestacao", "recurso_ordinario", "contrarrazoes", "embargos_declaracao",
                  "impugnacao_calculos", "embargos_execucao", "agravo_peticao", "recurso_revista"):
            self.assertIn(p, pecas)

    def test_sem_travessao_longo_nem_emoji(self):
        for area in banco.AREAS:
            for arq in (banco.BANCO / area).glob("*.json"):
                txt = arq.read_text(encoding="utf-8")
                self.assertNotIn("—", txt, f"travessao longo em {arq.name}")


class TestMontagem(unittest.TestCase):
    def test_toda_peca_monta_e_gera_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            for area in banco.AREAS:
                _, pecas = banco.carregar_area(area)
                for pid in pecas:
                    with self.subTest(area=area, peca=pid):
                        m = montar.montar(caso_completo(area, pid), escritorio.ESCRITORIO)
                        self.assertGreater(len(m["blocos"]), 5)
                        out = docx_fmt.gerar(m["blocos"], Path(tmp) / f"{area}_{pid}.docx",
                                             escritorio.FORMATO, None)
                        self.assertTrue(out.exists())
                        self.assertIn("Relatorio de conferencia", montar.relatorio(m))

    def test_toda_peca_seleciona_ao_menos_uma_tese_com_todas_as_tags(self):
        vazias = []
        for area in banco.AREAS:
            _, pecas = banco.carregar_area(area)
            for pid in pecas:
                m = montar.montar(caso_completo(area, pid), escritorio.ESCRITORIO)
                if not m["teses"]:
                    vazias.append(f"{area}/{pid}")
        self.assertEqual(vazias, [], f"pecas sem nenhuma tese: {vazias}")

    def test_lacunas_ficam_marcadas(self):
        caso = caso_completo("trabalhista_empresa", "contestacao")
        caso["reu"]["qualificacao"] = ""
        m = montar.montar(caso, escritorio.ESCRITORIO)
        self.assertIn("reu.qualificacao", m["faltantes"])
        self.assertTrue(any("●" in b["t"] for b in m["blocos"]))

    def test_incompativeis_geram_aviso(self):
        caso = caso_completo("trabalhista_empresa", "contestacao", todas_tags=False)
        caso["pedidos"] = ["horas_extras", "cargo_confianca", "trabalho_externo"]
        m = montar.montar(caso, escritorio.ESCRITORIO)
        self.assertTrue(any("INCOMPATIVEIS" in a for a in m["avisos"]))

    def test_exclusao_e_forcada(self):
        caso = caso_completo("trabalhista_empresa", "contestacao", todas_tags=False)
        caso["teses_forcadas"] = ["vinculo-inexistente-autonomo-pj"]
        caso["teses_excluidas"] = ["prescricao-bienal-quinquenal"]
        ids = {t["id"] for t in montar.montar(caso, escritorio.ESCRITORIO)["teses"]}
        self.assertIn("vinculo-inexistente-autonomo-pj", ids)
        self.assertNotIn("prescricao-bienal-quinquenal", ids)


class TestPrazos(unittest.TestCase):
    def test_pascoa(self):
        self.assertEqual(prazos.pascoa(2026), date(2026, 4, 5))

    def test_oito_dias_uteis_pula_fim_de_semana(self):
        # quarta 10/06/2026 + 8 dias uteis; 11/06 (corpus christi 04/06? nao) - so confere o resultado
        fim = prazos.calcular(date(2026, 6, 10), 8, "clt")
        self.assertEqual(fim.weekday() < 5, True)
        self.assertGreater(fim, date(2026, 6, 18))

    def test_recesso_clt(self):
        fim = prazos.calcular(date(2026, 12, 18), 5, "clt")
        self.assertGreaterEqual(fim, date(2027, 1, 7))


if __name__ == "__main__":
    unittest.main()
