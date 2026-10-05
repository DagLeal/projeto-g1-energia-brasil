# ⚡ Produção de Energia no Brasil

Projeto G1 — Análise e Visualização de Dados com Python (Tema 6)

| | |
|---|---|
| **Disciplina** | Linguagens de Programação |
| **Professor** | Alexandre Neves Louzada |
| **Aluno** | Dagner Costa Leal |

## Links
- Repositório: https://github.com/DagLeal/projeto-g1-energia-brasil
- Página do projeto (GitHub Pages): https://DagLeal.github.io/projeto-g1-energia-brasil/
- Dashboard (Streamlit): https://https://projeto-g1-energia-brasil-dag-leal.streamlit.app/

## Problema
Como a produção de energia se distribui entre regiões, estados e fontes, e como evolui ao longo do tempo?

## Base de dados
`dados/simulacao_producao_energia_brasil.csv` — base **simulada** fornecida pelo professor (14.400 linhas, 13 colunas).
Fonte: https://github.com/AlexandreLouzada/Dados-Simulados-G1

## Principais resultados
- Produção total de ≈ 571,8 milhões de MWh (2015–2024), com crescimento de ≈ 45% entre o primeiro e o último ano.
- A hidrelétrica é a maior fonte (≈ 212 milhões de MWh), seguida de termelétrica, eólica, solar, biomassa e nuclear.
- O Nordeste lidera a produção entre as regiões; o Sul tem a menor.
- ≈ 79% da produção é renovável (média ponderada); a termelétrica responde por ≈ 79% das emissões de CO₂.
- A produção tem correlação muito alta com consumo e capacidade instalada, e moderada (≈ 0,21) com emissões.

## Tecnologias
Python, Pandas, NumPy, Matplotlib, Seaborn, Streamlit, SQLAlchemy + SQLite, GitHub, GitHub Pages, Streamlit Community Cloud.

## Funcionalidades
**Intermediárias:** filtros múltiplos, KPIs dinâmicos, análise temporal, dashboard em seções (abas), visualizações comparativas, upload de arquivo.
**Avançadas:** persistência em banco (SQLAlchemy + SQLite), correlação estatística (Pearson) e séries temporais avançadas (média móvel de 12 meses e variação anual).

## Estrutura
```
projeto-g1/
├── app.py            # dashboard Streamlit
├── requirements.txt
├── README.md
├── index.html        # página de apresentação
├── dados/            # CSV
├── database/         # SQLite (gerado pelo app)
├── notebooks/        # análise (.ipynb)
└── imagens/          # prints e gráficos
```

## Como executar
```bash
pip install -r requirements.txt
streamlit run app.py
```

---
Autor: Dagner Costa Leal · Disciplina: Linguagens de Programação · Professor: Alexandre Neves Louzada
