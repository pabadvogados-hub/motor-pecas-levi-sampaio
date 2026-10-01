# Esquema do banco (leia antes de editar)

Cada area tem 3 arquivos em `banco/<area>/`:

| arquivo      | conteudo |
|--------------|----------|
| `teses.json` | lista de teses (blocos de argumentacao reaproveitaveis) |
| `pecas.json` | dict `peca_id -> especificacao` (estrutura da peca) |
| `tags.json`  | dict `tag -> descricao` (vocabulario de pedidos/temas que o caso pode citar) |

Valide sempre com `python -m motor validar`.

## Tese (`teses.json`)

```json
{
  "id": "horas-extras-controle-ponto",
  "titulo": "Horas extras - controle de jornada valido",
  "peca": ["contestacao", "recurso_ordinario"],
  "tipo": "merito",
  "ordem": 310,
  "tags": ["horas_extras"],
  "gatilhos": ["horas extras", "jornada", "sobrejornada"],
  "sempre": false,
  "incompativel_com": ["horas-extras-trabalho-externo-art62"],
  "texto": "Paragrafos prontos, com {{reu}} e {{data_admissao}}. Use [●] para o que o advogado preenche.",
  "pedido_defesa": "a improcedencia do pedido de horas extras e reflexos",
  "fundamentos": ["art. 74, par. 2o, CLT", "art. 818 CLT"],
  "jurisprudencia": ["Sumula 338 do TST"],
  "prova": ["cartoes de ponto de todo o contrato"],
  "riscos": "Cartoes britanicos invalidam a defesa (Sumula 338, III).",
  "conferir": ["valores vigentes", "tese ainda em disputa no TST"]
}
```

Campos obrigatorios: `id titulo peca tipo tags texto fundamentos`.

* `tipo`: `preliminar`, `prejudicial` (prescricao, decadencia), `merito`, `recursal`, `inicial`, `execucao`.
* `ordem`: posicao dentro da secao (menor = antes). Preliminares 100-199, prejudiciais 200-299, merito 300-899, gerais 900+.
* `tags`: o pedido/tema que ativa a tese. Devem existir em `tags.json`.
* `gatilhos`: palavras que, se aparecerem nos fatos do caso, **sugerem** a tese (entra marcada como sugerida).
* `sempre`: entra em toda peca listada (ex.: impugnacao generica de documentos, honorarios).
* `incompativel_com`: ids que nao podem coexistir (o motor avisa).
* `texto`: redacao-base em portugues juridico, impessoal, completa o bastante para ser usada como esta.
  Placeholders `{{campo}}` / `{{campo.sub}}` vem do caso; lacunas manuais ficam como `[●]`.
* `fundamentos`: normas (artigo + diploma). `jurisprudencia`: sumulas/OJs/temas.
  **So cite o que voce tem certeza que existe e diz aquilo.** Duvida -> ponha em `conferir`.
* `conferir`: pontos que o advogado deve checar antes de protocolar (valores, tese em disputa, mudanca recente).

## Peca (`pecas.json`)

```json
"contestacao": {
  "nome": "Contestacao trabalhista (reclamada)",
  "papel": "reu",
  "prazo": "ate a audiencia (art. 847 CLT) / prazo fixado no PJe",
  "enderecamento": "EXCELENTISSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA {{vara}}",
  "secoes": [
    {"id": "qualif", "titulo": null, "tipo": "texto", "texto": "{{reu.nome}}, ..., vem, por seu advogado, ..."},
    {"id": "sintese", "titulo": "I - SINTESE DA INICIAL", "tipo": "fatos_autor"},
    {"id": "prelim", "titulo": "II - PRELIMINARES", "tipo": "teses", "filtro": {"tipo": ["preliminar"]}},
    {"id": "merito", "titulo": "IV - MERITO", "tipo": "teses", "filtro": {"tipo": ["merito"]}},
    {"id": "pedidos", "titulo": "V - PEDIDOS", "tipo": "pedidos", "fixos": ["a intimacao ..."]},
    {"id": "fecho", "titulo": null, "tipo": "fecho"}
  ],
  "campos_obrigatorios": ["reu.nome", "autor.nome", "vara"],
  "documentos": ["procuracao e carta de preposicao", "contrato social", "cartoes de ponto"],
  "alertas": ["Impugnar especificamente cada fato (art. 341 CPC)."]
}
```

Tipos de secao: `texto`, `fatos_autor`, `fatos_reu`, `teses` (com `filtro.tipo`), `pedidos`, `fecho`.
`texto` aceita placeholders. `pedidos` junta `pedido_defesa` das teses escolhidas + a lista `fixos`.

## Regras de conteudo (valem para qualquer area)

1. **Nunca invente** numero de sumula, tema, artigo, ementa, processo ou valor. Sem certeza -> `conferir`.
2. Nada de dados reais de cliente. O banco e generico.
3. Texto impessoal, formal, sem travessao longo, sem emoji.
4. Cada tese deve funcionar sozinha e ser curta o bastante para o advogado adaptar (2 a 6 paragrafos).
5. Se a tese depende de fato que so o caso traz, deixe `[●]` e diga em `riscos` o que provar.
