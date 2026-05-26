# Degradação de Eficiência Paralela por SMT e Cache L3 em Processadores Híbridos

![Status](https://img.shields.io/badge/Status-Em%20andamento-yellow)
![Disciplina](https://img.shields.io/badge/CESAR%20School-Infraestrutura%20de%20Hardware%202026.1-green)

Artigo científico produzido para a 2ª Unidade da disciplina **Infraestrutura de Hardware**  
(CESAR School, 2026.1, Prof. Ronierison Maciel).  
Autor: **Rafael Coutinho Lima** — trabalho individual, Trilha A.

---

## Pergunta de pesquisa

> Qual é o impacto quantitativo do SMT (HyperThreading) e da contenção de cache L3
> na eficiência de paralelismo em cargas CPU-bound em processadores híbridos Intel de 13ª geração?

| | Hipótese |
|---|---|
| **H0** | O uso de threads lógicas além dos núcleos físicos **não** degrada significativamente a eficiência paralela (p ≥ 0,05). |
| **H1** | O uso de SMT causa degradação **estatisticamente significativa** de eficiência, especialmente acima de 10 threads (p < 0,05). |

---

## Hardware

| Componente | Especificação |
|---|---|
| CPU | Intel Core i7-13620H — Raptor Lake-H (13ª geração) |
| Arquitetura | Híbrida: 6 P-cores (HT) + 4 E-cores = 10 físicos / 16 lógicos |
| Cache L3 | 24 MB compartilhado |
| RAM | 15 GB DDR5 |
| SO | Ubuntu 25.10 |
| CPU Governor | `performance` |

---

## Como reproduzir

```bash
# 1. Clonar e preparar ambiente
git clone https://github.com/RafaelCoutinhoLima/Artigo_De_Hardware.git
cd Artigo_De_Hardware
python3 -m venv venv && source venv/bin/activate
pip install numpy scipy pandas matplotlib seaborn

# 2. Instalar ferramentas do sistema
sudo apt install sysbench mbw linux-tools-common
sudo cpupower frequency-set -g performance

# 3. Rodar experimento (~1h)
python scripts/experimento_principal.py

# 4. Análise estatística
python scripts/analise_estatistica.py

# 5. Gerar gráficos
python scripts/gerar_graficos.py
```

---

## Estrutura

```
.
├── artigo/
│   └── artigo.md                  # Manuscrito completo (IMRaD)
├── scripts/
│   ├── experimento_principal.py   # Coleta de dados (30 reps + warmup)
│   ├── analise_estatistica.py     # Estatísticas + testes de hipótese
│   └── gerar_graficos.py          # Figuras PNG 300 DPI
├── dados/
│   ├── raw/                       # CSVs brutos (não modificar)
│   └── processado/                # Resumo estatístico + testes
├── dados_piloto/                  # Coletas iniciais (histórico)
└── graficos/                      # Figuras do artigo
```

---

## Principais achados

- **Sysbench (strong scaling):** throughput estagna em ~13.870 ev/s a partir de 10 threads — diferença de apenas 0,02% entre 10 e 16 threads (p = 0,804, teste t pareado). SMT não contribui com throughput adicional em cargas CPU-bound.
- **Eficiência:** cai de 90,6% com 10 threads para 56,7% com 16 threads — degradação de 34 pontos percentuais.
- **Weak scaling (Python multiprocessing):** overhead do método `spawn` (~0,1–0,2 s/processo) domina para tarefas curtas, resultando em eficiência de apenas 11,7% com 16 processos.

---

## Licença

MIT License + CC BY 4.0 para dados e manuscrito.
