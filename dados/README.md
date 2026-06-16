# Dados do experimento

Dados brutos e processados do estudo de eficiencia paralela (SMT + cache L3) no Intel i7-13620H.

## `raw/` — dados brutos (nao modificar)

| Arquivo | Colunas | Descricao |
|---|---|---|
| `paralelismo_raw.csv` | `n_threads, repeticao, tempo_s` | Tempo (s) de cada bloco de N multiplicacoes de matrizes 800x800 (weak scaling). 30 repeticoes por N. |
| `sysbench_raw.csv` | `n_threads, repeticao, events_per_sec` | Throughput (events/s) do `sysbench cpu` por repeticao (strong scaling). 30 repeticoes por N. |
| `ambiente.txt` | — | Captura do ambiente: SO/kernel, CPU (`lscpu`), memoria, storage, governor, versoes das ferramentas. |
| `experimento_log.txt` | — | Log completo da execucao (warm-up + 30 medicoes por N). |

`n_threads` assume os valores {1, 2, 4, 6, 8, 10, 12, 14, 16}. As 3 primeiras execucoes
de cada bloco (warm-up) sao descartadas e nao aparecem nos CSV.

## `processado/` — resultados derivados

| Arquivo | Conteudo |
|---|---|
| `resumo_estatistico.csv` | Por (metrica, n_threads): media, desvio-padrao, SEM, IC 95% (t de Student), speedup e eficiencia. |
| `testes_hipotese.csv` | Testes t pareado e Wilcoxon para as comparacoes 1 vs 10 e 10 vs 16 threads. |

## Reproducao

```bash
python scripts/experimento_principal.py   # gera raw/
python scripts/analise_estatistica.py      # gera processado/
python scripts/gerar_graficos.py           # gera graficos/
```
