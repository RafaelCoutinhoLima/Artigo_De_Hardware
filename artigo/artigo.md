# Degradação de Eficiência Paralela por Contenção de Cache L3 e SMT em Processadores Híbridos: Estudo Empírico no Intel i7-13620H

**Autor:** Rafael Coutinho Lima
**Instituição:** CESAR School — Bacharelado em Ciência da Computação
**Disciplina:** Infraestrutura de Hardware (2026.1)
**Orientação:** Prof. Ronierison Maciel
**Data:** 25/05/2026

---

## Resumo

Este artigo investiga quantitativamente o impacto do Simultaneous Multithreading (SMT/HyperThreading) e da contenção de cache L3 na eficiência de paralelismo em cargas CPU-bound no processador Intel Core i7-13620H (13ª geração, arquitetura híbrida Raptor Lake-H). Foram realizadas 30 repetições medidas por configuração de threads ∈ {1, 2, 4, 6, 8, 10, 12, 14, 16}, precedidas de 3 aquecimentos descartados. Dois experimentos foram conduzidos: (A) multiplicação de matrizes 800×800 via `multiprocessing.Pool` em escalonamento fraco (*weak scaling*), e (B) benchmark `sysbench cpu` em escalonamento forte (*strong scaling*). No experimento sysbench, o throughput aumenta de 1530,0 para 13866,8 eventos/s ao escalar de 1 para 10 threads (eficiência 90,6%), mas **estagna** em 13870,0 eventos/s com 16 threads — diferença de apenas 0,02% entre 10 e 16 threads (p = 0.804253, teste t pareado). A eficiência por thread cai de 90,6% (10 threads) para 56,7% (16 threads), confirmando que o SMT não contribui com throughput adicional em cargas puramente CPU-bound. No experimento de weak scaling, o overhead de criação de processos Python (`spawn`) domina, com eficiência de apenas 11,7% com 16 processos. Todos os dados e scripts estão publicamente disponíveis para reprodução.

**Palavras-chave:** SMT; eficiência paralela; contenção de cache; processadores híbridos; avaliação de desempenho.

---

## 1. Introdução

A adoção crescente de processadores híbridos — que combinam núcleos de alta performance (P-cores) e núcleos de eficiência energética (E-cores) — introduz desafios novos na avaliação de desempenho paralelo. O Intel Core i7-13620H (Raptor Lake-H, 13ª geração) possui 6 P-cores com SMT (12 threads lógicas) e 4 E-cores sem SMT (4 threads), totalizando 16 threads lógicas sobre 10 núcleos físicos.

O Simultaneous Multithreading (SMT), comercialmente denominado HyperThreading pela Intel, permite que dois threads lógicos compartilhem os recursos de execução de um único núcleo físico. Em cargas mistas (CPU + I/O), o SMT pode aumentar a utilização do pipeline ocultando latências de memória. Porém, em cargas estritamente CPU-bound, dois threads lógicos competem pelos mesmos recursos de execução, cache L1/L2 privado e entradas do TLB — sem ganho de throughput proporcional. Além disso, ao escalar além dos núcleos P-cores físicos, os threads passam a compartilhar mais intensamente o cache L3 (24 MB compartilhado), podendo causar contenção e evicções frequentes.

Este trabalho responde à seguinte **pergunta de pesquisa**: *Qual é o impacto quantitativo do SMT e da contenção de cache L3 na eficiência de paralelismo em cargas CPU-bound em processadores híbridos Intel de 13ª geração?*

**Hipóteses:**

- **H0 (hipótese nula):** O uso de threads lógicas além dos núcleos físicos não degrada significativamente a eficiência paralela nem o throughput (p ≥ 0,05).
- **H1 (hipótese alternativa):** O uso de SMT causa degradação estatisticamente significativa de eficiência, especialmente acima de 10 threads — limite dos P-cores físicos (p < 0,05).

---

## 2. Trabalhos Relacionados

O impacto do SMT em cargas CPU-bound foi documentado por Tullsen et al. [1],
que introduziram o conceito de multithreading simultâneo no ISCA 1995,
demonstrando ganhos em workloads com alta latência de memória mas limitações
em cargas compute-bound. Eyerman e Eeckhout [2] propuseram uma arquitetura de
contabilização de ciclos por thread (*per-thread cycle accounting*) em
processadores SMT, mostrando como cada thread é penalizada ao compartilhar
recursos de execução — base para entender por que a competição por unidades
funcionais reduz os ganhos do SMT em cargas CPU-intensivas.

A contenção de cache compartilhado em sistemas multicore foi estudada por
Blagodurov et al. [3], que demonstraram degradação de desempenho proporcional
ao número de threads competindo pelo mesmo nível de cache — resultado
consistente com os dados coletados neste trabalho para o L3 de 24 MB do
i7-13620H.

Hill e Marty [4] revisitaram a Lei de Amdahl no contexto de multicores,
mostrando que a fração serial do programa limita o speedup independentemente
do número de núcleos — o que se manifesta aqui como o plateau observado
a partir de 10 threads. Para o escalonamento fraco, Gustafson [5] demonstrou
que o overhead de criação de processos é um fator dominante em tarefas de
curta duração, o que explica a eficiência de apenas 11,7% observada com
16 processos Python via `spawn`.

A arquitetura híbrida Intel (P-cores + E-cores), introduzida no Alder Lake
e presente no i7-13620H (Raptor Lake), é descrita em detalhe pela Intel [6],
incluindo o mecanismo Thread Director que orienta o escalonador Linux na
distribuição de cargas entre os dois tipos de núcleo. Por fim, Mytkowicz et al. [7]
demonstraram que fatores aparentemente inócuos do ambiente de medição
(configurações de SO e hardware, variáveis de ambiente) podem enviesar
resultados de benchmarks, o que motivou o controle de ambiente adotado aqui —
modo `performance` do governor, descarte de *warm-up* e 30 repetições por configuração.

---

## 3. Metodologia

### 3.1 Hardware

| Componente | Especificação |
|---|---|
| Processador | Intel Core i7-13620H (Raptor Lake-H, 13ª geração) |
| Núcleos físicos | 10 (6 P-cores + 4 E-cores) |
| Threads lógicas | 16 (P-cores com SMT 2×; E-cores sem SMT) |
| Cache L1d | 416 KiB (10 instâncias) |
| Cache L1i | 448 KiB (10 instâncias) |
| Cache L2 | 9,5 MiB (7 instâncias) |
| Cache L3 | 24 MiB (1 instância, compartilhado) |
| Memória RAM | 14 GiB DDR5 |
| Armazenamento | NVMe PCIe Gen4 |

### 3.2 Software

| Componente | Versão |
|---|---|
| SO | Ubuntu Linux |
| Python | 3.13 |
| numpy | 2.4.4 |
| scipy | 1.17.1 |
| pandas | 3.0.3 |
| sysbench | 1.0.20 |
| CPU governor | `performance` (`cpupower frequency-set -g performance`) |

### 3.3 Protocolo Experimental

Para cada N ∈ {1, 2, 4, 6, 8, 10, 12, 14, 16} threads:
1. **Aquecimento:** 3 execuções completas descartadas.
2. **Medições:** 30 execuções cronometradas.
3. **Resfriamento:** pausa de 2 s entre blocos.

**Experimento A — Multiplicação de matrizes (weak scaling):**
N processos independentes via `multiprocessing.Pool` realizam cada um uma multiplicação de matrizes densas 800×800 (`numpy`). O tempo medido é o do bloco completo. Em *weak scaling*, o trabalho total escala com N; speedup ideal = 1,0 (TN = T1). O método de criação de processos utilizado foi `spawn` (padrão seguro no Linux), cujo overhead de inicialização é um resultado em si.

**Experimento B — sysbench CPU (strong scaling):**
`sysbench cpu --cpu-max-prime=20000 --threads=N --time=10 run`. O workload é fixo; N threads trabalham na mesma carga. Métrica: *events/second*. Speedup = EPS_N / EPS_1; eficiência = Speedup / N.

### 3.4 Análise Estatística

Para cada (N, métrica): média, DP amostral (ddof=1), IC 95% via t de Student (`scipy.stats.t.interval`).

Testes de hipótese (α = 0,05):
- **Teste t pareado** (`scipy.stats.ttest_rel`)
- **Teste de Wilcoxon** (`scipy.stats.wilcoxon`) — não-paramétrico

Comparações centrais: 1 vs 10 threads; 10 vs 16 threads.

---

## 4. Resultados

### 4.1 Tabela 1 — Experimento A: Multiplicação de Matrizes (weak scaling)

| Threads | Média (s) | DP (s) | IC 95% | Speedup_weak | Efic. (%) |
|---------|-----------|--------|--------|-------------|-----------|
| 1 | 0,094 | 0,015 | [0,089, 0,100] | 1,00 | 100,0 |
| 2 | 0,201 | 0,013 | [0,196, 0,206] | 0,94 | 46,9 |
| 4 | 0,310 | 0,027 | [0,300, 0,320] | 1,22 | 30,4 |
| 6 | 0,410 | 0,031 | [0,398, 0,421] | 1,38 | 23,0 |
| 8 | 0,519 | 0,024 | [0,510, 0,528] | 1,45 | 18,1 |
| 10 | 0,638 | 0,027 | [0,628, 0,648] | 1,48 | 14,8 |
| 12 | 0,703 | 0,027 | [0,693, 0,713] | 1,61 | 13,4 |
| 14 | 0,745 | 0,043 | [0,728, 0,761] | 1,77 | 12,6 |
| 16 | 0,805 | 0,030 | [0,794, 0,816] | 1,87 | 11,7 |

*Speedup_weak = (N × T₁) / T_N; eficiência ideal = 100% (T_N = T₁).*

Com 2 processos, o speedup cai para 0,94 (46,9% de eficiência) — o overhead de criação de processos `spawn` (~0,1 s por processo) supera o ganho de paralelismo para tarefas desta duração. A eficiência cai monotonicamente até 11,7% com 16 processos, com speedup weak de apenas 1,87×. Figuras 1 e 2 ilustram a curva de eficiência e speedup com barras de erro IC 95%.

### 4.2 Tabela 2 — Experimento B: sysbench CPU (strong scaling)

| Threads | Média (ev/s) | DP (ev/s) | IC 95% | Speedup | Efic. (%) |
|---------|-------------|-----------|--------|---------|-----------|
| 1 | 1530,0 | 1,8 | [1529,3, 1530,6] | 1,00 | 100,0 |
| 2 | 3047,7 | 7,0 | [3045,0, 3050,3] | 1,99 | 99,6 |
| 4 | 5913,1 | 6,0 | [5910,8, 5915,3] | 3,86 | 96,6 |
| 6 | 8866,1 | 5,9 | [8863,9, 8868,4] | 5,80 | 96,6 |
| 8 | 11401,0 | 31,2 | [11389,3, 11412,6] | 7,45 | 93,1 |
| 10 | 13866,8 | 27,1 | [13856,7, 13876,9] | 9,06 | 90,6 |
| 12 | 13831,1 | 83,5 | [13800,0, 13862,3] | 9,04 | 75,3 |
| 14 | 13824,4 | 85,8 | [13792,4, 13856,5] | 9,04 | 64,5 |
| 16 | 13870,0 | 66,5 | [13845,2, 13894,8] | 9,07 | 56,7 |

O throughput cresce quase linearmente até 10 threads (speedup 9,06×, eficiência 90,6%), mas **estagna** a partir de 10 threads: com 12, 14 e 16 threads o valor permanece praticamente idêntico ao de 10 threads. Figura 4 detalha a curva de throughput.

### 4.3 Tabela 3 — Testes de Hipótese (α = 0,05)

| Métrica | Comparação | Teste | Estatística | p-valor | Rejeita H0? |
|---------|-----------|-------|------------|---------|------------|
| paralelismo_tempo | 1vs10 | t_pareado | -89.7676 | < 0.001 | **sim** |
| paralelismo_tempo | 1vs10 | wilcoxon | 0.0 | < 0.001 | **sim** |
| paralelismo_tempo | 10vs16 | t_pareado | -21.7264 | < 0.001 | **sim** |
| paralelismo_tempo | 10vs16 | wilcoxon | 0.0 | < 0.001 | **sim** |
| sysbench_eps | 1vs10 | t_pareado | -2448.2937 | < 0.001 | **sim** |
| sysbench_eps | 1vs10 | wilcoxon | 0.0 | < 0.001 | **sim** |
| sysbench_eps | 10vs16 | t_pareado | -0.2501 | 0.804253 | **não** |
| sysbench_eps | 10vs16 | wilcoxon | 168.0 | 0.19093 | **não** |

O resultado mais relevante é **sysbench 10 vs 16 threads**: p = 0.804253 (t pareado) e p = 0.19093 (Wilcoxon) — **não rejeita H0** para throughput. Isso significa que adicionar threads via SMT (11–16) **não melhora significativamente** o throughput do sysbench. Porém, a eficiência por thread cai de 90,6% para 56,7%, uma degradação de 34,0 pontos percentuais — confirmando H1 no quesito eficiência.

---

## 5. Discussão

### 5.1 Achado Principal: Plateau de Throughput por SMT

O resultado mais claro do experimento é o plateau de throughput no sysbench a partir de 10 threads (limite dos P-cores físicos). De 10 para 16 threads, o throughput varia apenas 0,02% — variação não significativa (p = 0.804253). Isso demonstra que, para cargas puramente CPU-bound, o SMT no i7-13620H **não contribui com capacidade computacional adicional**: os dois threads lógicos por P-core compartilham as mesmas unidades de execução, e ambos competem por tempo de CPU sem que o pipeline fique ocioso (ao contrário de cargas mistas).

A degradação de eficiência (de 90,6% com 10 threads para 56,7% com 16 threads) é consequência direta: o denominador cresce (mais threads), mas o numerador (throughput) não. Isso tem implicação prática direta: configurar pool de threads igual ao número de threads lógicas (16) em vez do número de P-cores (10) desperdiça 34,0 pontos percentuais de eficiência sem nenhum ganho de velocidade.

### 5.2 Overhead de Processos Python (Weak Scaling)

O experimento A revelou que o overhead de criação de processos Python com o método `spawn` (~0,1–0,2 s por processo) supera o benefício de paralelismo para tarefas de curta duração (T₁ ≈ 0,094 s). Com 2 processos, o tempo total (0,201 s) é maior do que executar 2 tarefas sequencialmente (2 × 0,094 = 0,188 s), resultando em eficiência de 46,9%. Este resultado ressalta uma limitação prática importante: em Python, `multiprocessing.Pool` com `spawn` é adequado apenas para tarefas com duração significativamente maior que o overhead de criação de processos (~0,5–1 s). Para tarefas curtas, técnicas como pool pré-aquecido ou `concurrent.futures.ThreadPoolExecutor` (para workloads não-GIL) seriam mais eficientes.

### 5.3 Contenção de Cache L3

Cada processo no experimento A aloca duas matrizes 800×800 de float64 (~5,1 MB cada par). Com 4 processos: ~20,5 MB de dados ativos — próximo ao limite do L3 (24 MB). Com 10+ processos, os dados excedem o L3, forçando acessos à DRAM. Os dados de largura de banda (Fig. 3, mbw) ilustram a diferença de banda ao escalar o tamanho do bloco de 16 MiB para 1.024 MiB, indicando que a hierarquia de cache é um fator relevante para a carga estudada. Ressalta-se, porém, que a contenção de L3 é aqui *inferida* a partir da relação entre o conjunto de trabalho e a capacidade do cache: não foram coletados contadores de *last-level cache miss* via `perf`, ficando a quantificação direta como trabalho futuro.

### 5.4 Comparação com Dados Piloto

Os dados piloto anteriores (governor `powersave`, sem repetições formais) registravam anomalia em 16 threads (speedup 1,89× frente a ~2,52× em 4 threads). Os dados desta coleta confirmam o padrão geral: a eficiência degradada progressivamente com o aumento de threads é um resultado robusto, não artefato do governor.

### 5.5 Limitações

- **Única máquina:** sem comparação com AMD Zen 4 ou outra geração Intel.
- **Método `spawn`:** no experimento A, o overhead de criação domina. Resultados com `fork` seriam diferentes (menor overhead, porém potencialmente menos seguro em ambientes com múltiplas threads).
- **Sem isolamento de CPU:** não foram usados `taskset`/`numactl`. O escalonador Linux (CFS+ITMT) pode ter distribuído threads entre P-cores e E-cores de forma não determinística.
- **Turbo Boost:** pode elevar frequências de forma variável, introduzindo variabilidade não controlada mesmo com governor `performance`.
- **Sem comparação AMD:** a arquitetura híbrida Intel (P+E cores) difere fundamentalmente de CPUs homogêneas. Resultados podem não generalizar.

---

## 6. Conclusão

Este estudo demonstrou empiricamente dois efeitos distintos no Intel Core i7-13620H:

1. **SMT não melhora throughput CPU-bound:** O teste sysbench confirma que adicionar threads via SMT (10→16) não produz aumento significativo de throughput (p = 0.804253), mas degrada a eficiência por thread de 90,6% para 56,7%.

2. **Overhead de processos Python domina em tarefas curtas:** O método `spawn` do `multiprocessing.Pool` introduz overhead que supera o benefício de paralelismo para tarefas com T₁ < 0,5 s.

**Resposta à pergunta de pesquisa:** Para cargas CPU-bound neste processador, o SMT **não melhora throughput** (H0 não rejeitada para throughput, p = 0.804253) mas **degrada eficiência** por thread em 34,0 pontos percentuais (H1 confirmada para eficiência). A recomendação prática é limitar pools de processos/threads ao número de P-cores físicos (10 no i7-13620H), não ao total de threads lógicas.

Trabalhos futuros devem investigar: (i) comparação com método `fork` para avaliar custo de spawn isoladamente; (ii) CPUs AMD Zen 4 (homogêneas) na mesma carga; (iii) cargas mistas CPU+I/O onde o SMT pode apresentar ganhos; (iv) isolamento via `taskset` para controlar a distribuição entre P-cores e E-cores.

---

## Disponibilidade de Artefatos

Scripts, dados brutos (CSV) e gráficos disponíveis em:
**https://github.com/RafaelCoutinhoLima/Artigo_De_Hardware**

---

## Referências

[1] TULLSEN, D. M.; EGGERS, S. J.; LEVY, H. M. Simultaneous multithreading:
maximizing on-chip parallelism. In: **Proceedings of the 22nd Annual
International Symposium on Computer Architecture (ISCA)**, 1995,
p. 392–403. DOI: 10.1145/223982.224449.

[2] EYERMAN, S.; EECKHOUT, L. Per-thread cycle accounting in SMT processors.
In: **Proceedings of the 14th International Conference on Architectural Support
for Programming Languages and Operating Systems (ASPLOS)**, 2009, p. 133–144.
DOI: 10.1145/1508244.1508260.

[3] BLAGODUROV, S.; ZHURAVLEV, S.; DASHTI, M.; FEDOROVA, A. A case for
NUMA-aware contention management on multicore systems. In: **Proceedings of
the 2011 USENIX Annual Technical Conference (USENIX ATC)**, 2011.

[4] HILL, M. D.; MARTY, M. R. Amdahl's law in the multicore era.
**IEEE Computer**, v. 41, n. 7, p. 33–38, jul. 2008.
DOI: 10.1109/MC.2008.209.

[5] GUSTAFSON, J. L. Reevaluating Amdahl's law. **Communications of the ACM**,
v. 31, n. 5, p. 532–533, maio 1988. DOI: 10.1145/42411.42415.

[6] INTEL CORPORATION. **Intel® Core™ 13th Generation Processor
Product Brief: Raptor Lake**. Santa Clara: Intel, 2022. Disponível em:
https://www.intel.com/content/www/us/en/products/docs/processors/core/
13th-gen-core-mobile-processors-brief.html. Acesso em: 25 maio 2026.

[7] MYTKOWICZ, T.; DIWAN, A.; HAUSWIRTH, M.; SWEENEY, P. F. Producing wrong
data without doing anything obviously wrong! In: **Proceedings of the 14th
International Conference on Architectural Support for Programming Languages
and Operating Systems (ASPLOS)**, 2009, p. 265–276. DOI: 10.1145/1508244.1508275.

[8] KOPYTOV, A. **SysBench: A Scriptable Database and System Performance
Benchmark**. Versão 1.0.20. Disponível em: https://github.com/akopytov/sysbench.
Acesso em: 25 maio 2026.
