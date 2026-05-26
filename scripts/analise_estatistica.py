#!/usr/bin/env python3
# Fase 2 — Análise Estatística
# Lê os CSVs brutos e produz resumo estatístico + testes de hipótese.

import pandas as pd
import numpy as np
from scipy import stats
import os

RAW_DIR   = os.path.join(os.path.dirname(__file__), "..", "dados", "raw")
PROC_DIR  = os.path.join(os.path.dirname(__file__), "..", "dados", "processado")
CSV_PAR   = os.path.join(RAW_DIR, "paralelismo_raw.csv")
CSV_SYS   = os.path.join(RAW_DIR, "sysbench_raw.csv")
CSV_RESUMO = os.path.join(PROC_DIR, "resumo_estatistico.csv")
CSV_TESTES = os.path.join(PROC_DIR, "testes_hipotese.csv")


def resumo_grupo(df: pd.DataFrame, val_col: str) -> pd.DataFrame:
    """Calcula estatísticas por n_threads para uma métrica."""
    linhas = []
    for n, grupo in df.groupby("n_threads"):
        vals = grupo[val_col].values
        n_obs = len(vals)
        media = np.mean(vals)
        dp    = np.std(vals, ddof=1)
        sem   = stats.sem(vals)
        ci_lo, ci_hi = stats.t.interval(0.95, df=n_obs - 1, loc=media, scale=sem)
        linhas.append({
            "n_threads": n,
            "n_obs": n_obs,
            "media": media,
            "dp": dp,
            "sem": sem,
            "ic95_lo": ci_lo,
            "ic95_hi": ci_hi,
        })
    return pd.DataFrame(linhas)


def calcular_speedup_eficiencia(resumo: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Adiciona speedup e eficiência ao resumo.

    Para tempo (weak scaling): N processos fazem N tarefas em paralelo.
      Speedup_weak = (N * T1_1tarefa) / TN  → ideal = 1.0, eficiência ideal = 100%.
    Para events/s (strong scaling): throughput relativo a 1 thread.
      Speedup = EPS_N / EPS_1, eficiência = Speedup / N.
    """
    resumo = resumo.copy()
    if metrica == "tempo_s":
        # Weak scaling: tempo serial para N tarefas = N * T(1 thread, 1 tarefa)
        t1_1task = resumo.loc[resumo["n_threads"] == 1, "media"].values[0]
        n = resumo["n_threads"].values
        resumo["speedup"]    = (n * t1_1task) / resumo["media"]
        resumo["eficiencia"] = resumo["speedup"] / n
    elif metrica == "events_per_sec":
        t1 = resumo.loc[resumo["n_threads"] == 1, "media"].values[0]
        resumo["speedup"]    = resumo["media"] / t1
        resumo["eficiencia"] = resumo["speedup"] / resumo["n_threads"]
    return resumo


def executar_testes(df_par: pd.DataFrame, df_sys: pd.DataFrame) -> pd.DataFrame:
    """Testes t pareados e Wilcoxon para comparações centrais."""
    comparacoes = [
        ("paralelismo_tempo", "1vs10",  df_par, "tempo_s",        1,  10),
        ("paralelismo_tempo", "10vs16", df_par, "tempo_s",        10, 16),
        ("sysbench_eps",      "1vs10",  df_sys, "events_per_sec", 1,  10),
        ("sysbench_eps",      "10vs16", df_sys, "events_per_sec", 10, 16),
    ]

    linhas = []
    for metrica, comp, df, col, na, nb in comparacoes:
        a = df[df["n_threads"] == na][col].values
        b = df[df["n_threads"] == nb][col].values
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]  # empareamento por posição (mesma ordem de coleta)

        # Teste t pareado
        t_stat, t_p = stats.ttest_rel(a, b)
        linhas.append({
            "metrica": metrica, "comparacao": comp, "teste": "t_pareado",
            "statistic": round(t_stat, 4), "p_value": round(t_p, 6),
            "rejeita_H0": "sim" if t_p < 0.05 else "não"
        })

        # Wilcoxon
        try:
            w_stat, w_p = stats.wilcoxon(a, b)
        except ValueError as e:
            w_stat, w_p = float("nan"), float("nan")
        linhas.append({
            "metrica": metrica, "comparacao": comp, "teste": "wilcoxon",
            "statistic": round(w_stat, 4) if not np.isnan(w_stat) else "N/A",
            "p_value": round(w_p, 6) if not np.isnan(w_p) else "N/A",
            "rejeita_H0": ("sim" if w_p < 0.05 else "não") if not np.isnan(w_p) else "N/A"
        })

    return pd.DataFrame(linhas)


def main():
    os.makedirs(PROC_DIR, exist_ok=True)

    df_par = pd.read_csv(CSV_PAR)
    df_sys = pd.read_csv(CSV_SYS)

    # Resumo paralelismo
    res_par = resumo_grupo(df_par, "tempo_s")
    res_par = calcular_speedup_eficiencia(res_par, "tempo_s")
    res_par["metrica"] = "paralelismo_tempo_s"

    # Resumo sysbench
    res_sys = resumo_grupo(df_sys, "events_per_sec")
    res_sys = calcular_speedup_eficiencia(res_sys, "events_per_sec")
    res_sys["metrica"] = "sysbench_events_per_sec"

    resumo = pd.concat([res_par, res_sys], ignore_index=True)

    cols_ordem = ["metrica", "n_threads", "n_obs", "media", "dp", "sem",
                  "ic95_lo", "ic95_hi", "speedup", "eficiencia"]
    resumo = resumo[cols_ordem]
    resumo.to_csv(CSV_RESUMO, index=False, float_format="%.6f")

    # Testes de hipótese
    testes = executar_testes(df_par, df_sys)
    testes.to_csv(CSV_TESTES, index=False)

    # Resumo no terminal
    print("\n" + "="*70)
    print("RESUMO ESTATÍSTICO — PARALELISMO (tempo em segundos)")
    print("="*70)
    for _, row in res_par.iterrows():
        print(f"  {int(row['n_threads']):2d} threads | "
              f"média={row['media']:.3f}s ±{row['dp']:.3f} "
              f"IC95=[{row['ic95_lo']:.3f},{row['ic95_hi']:.3f}] | "
              f"speedup={row['speedup']:.2f} | efic={row['eficiencia']*100:.1f}%")

    print("\n" + "="*70)
    print("RESUMO ESTATÍSTICO — SYSBENCH (events/s)")
    print("="*70)
    for _, row in res_sys.iterrows():
        print(f"  {int(row['n_threads']):2d} threads | "
              f"média={row['media']:.1f} ±{row['dp']:.1f} "
              f"IC95=[{row['ic95_lo']:.1f},{row['ic95_hi']:.1f}] | "
              f"speedup={row['speedup']:.2f} | efic={row['eficiencia']*100:.1f}%")

    print("\n" + "="*70)
    print("TESTES DE HIPÓTESE (alpha=0.05)")
    print("="*70)
    for _, row in testes.iterrows():
        print(f"  {row['metrica']} | {row['comparacao']} | {row['teste']} | "
              f"stat={row['statistic']}  p={row['p_value']}  rejeita_H0={row['rejeita_H0']}")

    print(f"\n  → {CSV_RESUMO}")
    print(f"  → {CSV_TESTES}")


if __name__ == "__main__":
    main()
