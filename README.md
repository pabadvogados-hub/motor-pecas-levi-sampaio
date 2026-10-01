# Motor de Peças: Trabalhista (empresa e empregado), Cível e Família

Gera a minuta de peças processuais em .docx a partir de um banco de teses revisável, e (opcional) pede ao Claude que refine a minuta aos fatos do caso.

| Área | Teses | Peças |
|---|---|---|
| `trabalhista_empresa` (prioridade) | 81 | contestação, exceção de incompetência, recurso ordinário, contrarrazões, embargos de declaração, impugnação de cálculos, embargos à execução, agravo de petição, manifestação sobre laudo, razões finais, acordo extrajudicial, recurso de revista |
| `trabalhista_empregado` | 76 | reclamação, réplica, razões finais, recurso, embargos, agravo, cálculos |
| `civel` | 76 | iniciais (indenização, cobrança, obrigação de fazer/tutela, declaratória), contestação, réplica, apelação, agravo, cumprimento, embargos, exceção de pré-executividade |
| `familia` | 79 | divórcio, união estável, alimentos (ação, revisão, exoneração, execução), guarda, paternidade, alienação parental, inventário, apelação |

## Instalar
```
pip install -r requirements.txt
```
Edite `config/escritorio.py` (nome, OAB, cidade, formatação). Papel timbrado opcional: salve em `config/TIMBRADO.docx`.

## Usar
```
python -m motor areas
python -m motor pecas trabalhista_empresa
python -m motor tags trabalhista_empresa
python -m motor novo trabalhista_empresa contestacao -o saida/caso.json   # preencha o JSON
python -m motor gerar saida/caso.json      # .docx + relatório de conferência
python -m motor redigir saida/caso.json    # idem, refinado pelo Claude (ANTHROPIC_API_KEY no .env)
python -m motor prazo 30/09/2026 recurso_ordinario
python -m motor validar
```
No caso, `pedidos` lista as tags (temas) que a peça deve tratar. Teses `sempre`, as por tag e as por palavra-chave (marcadas "sugerida, revisar") entram na minuta. Lacunas aparecem em amarelo como `[campo ●]`.

## Regras de ouro
1. **Toda citação deve ser conferida** antes do protocolo. O relatório `_conferencia.md` lista cada norma/súmula e os pontos marcados `conferir` (valores vigentes, teses em disputa, Temas do STF).
2. O motor não inventa fato, valor ou jurisprudência; o Claude, no `redigir`, é instruído a marcar `[CONFERIR]` o que não estiver no banco.
3. O advogado responde pela peça. Isto é ferramenta de produtividade.
4. Prazos: a calculadora não conhece feriados locais; confirme no calendário do tribunal.

## Evoluir o banco
Veja `banco/_schema.md`. Cada tese é um JSON; ao editar rode `python -m motor validar` e `python -m unittest discover -s tests`.
Não há dados de clientes no banco; mantenha assim.
