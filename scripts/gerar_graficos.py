#!/usr/bin/env python3
# Fase 3 — Geração de Gráficos
# Lê dados processados e gera as 4 figuras do artigo (PNG 300 DPI).

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import re
from pathlib import Path

PROC_DIR   = Path(__file__).parent.parent / "dados" / "processado"
RAW_DIR    = Path(__file__).parent.parent / "dados" / "raw"
PILOTO_DIR = Path(__file__).parent.parent / "dados_piloto"
GRAF_DIR   = Path(__file__).parent.parent / "graficos"
GRAF_DIR.mkdir(exist_ok=True)

CSV_RESUMO = PROC_DIR / "resumo_estatistico.csv"

# Estilo global
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.family": "serif",
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 300,
})
LIMITE_FISICO = 10  # P-cores do i7-13620H


def carregar_resumo():
    df = pd.read_csv(CSV_RESUMO)
    par = df[df["metrica"] == "paralelismo_tempo_s"].copy()
    sys = df[df["metrica"] == "sysbench_events_per_sec"].copy()
    return par, sys


# ── Fig 1 — Eficiência por threads ────────────────────────────────────────────
def fig1_eficiencia(par):
    fig, ax = plt.subplots(figsize=(10, 6))

    threads = par["n_threads"].values
    efic    = par["eficiencia"].values * 100
    # IC 95% propagado para eficiência: ΔEfic ≈ (ic_hi - ic_lo) / 2 / T1 / N * 100
    t1_media = par.loc[par["n_threads"] == 1, "media"].values[0]
    err = ((par["ic95_hi"] - par["ic95_lo"]) / 2 / t1_media / par["n_threads"]) * 100

    ax.errorbar(threads, efic, yerr=err.values,
                fmt="o-", color="#2c7bb6", linewidth=2, markersize=6,
                capsize=4, label="Eficiência observada (IC 95%)")
    ax.axhline(100, color="gray", linestyle="--", linewidth=1.2, label="Eficiência ideal (100%)")
    ax.axvline(LIMITE_FISICO, color="#d7191c", linestyle=":", linewidth=1.5,
               label=f"Limite P-cores físicos ({LIMITE_FISICO})")

    # Anotação do SMT cliff
    idx10 = list(threads).index(LIMITE_FISICO) if LIMITE_FISICO in threads else -1
    idx16 = list(threads).index(16) if 16 in threads else -1
    if idx10 >= 0 and idx16 >= 0:
        ax.annotate(
            f"SMT cliff\n{efic[idx10]:.1f}% → {efic[idx16]:.1f}%",
            xy=(16, efic[idx16]),
            xytext=(13, efic[idx16] + 8),
            arrowprops=dict(arrowstyle="->", color="#d7191c"),
            fontsize=9, color="#d7191c"
        )

    ax.set_xlabel("Número de threads")
    ax.set_ylabel("Eficiência paralela (%)")
    ax.set_title("Fig. 1 — Eficiência paralela vs. número de threads\n(Multiplicação de matrizes 800×800, i7-13620H)")
    ax.set_xticks(threads)
    ax.legend(loc="upper right")
    fig.tight_layout()
    path = GRAF_DIR / "fig1_eficiencia_threads.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Salvo: {path}")


# ── Fig 2 — Speedup vs Amdahl ─────────────────────────────────────────────────
def fig2_speedup_amdahl(par):
    fig, ax = plt.subplots(figsize=(10, 6))

    threads = par["n_threads"].values
    speedup = par["speedup"].values
    t1      = par.loc[par["n_threads"] == 1, "media"].values[0]
    err_sp  = ((par["ic95_hi"] - par["ic95_lo"]) / 2 / t1).values

    # Estimar fração serial f via mínimos quadrados em 1/S = f + (1-f)/N
    # → f = (1/S - 1/N) / (1 - 1/N)
    inv_s = 1.0 / speedup
    inv_n = 1.0 / threads
    # Regressão linear: 1/S ~ f + (1-f)/N  → 1/S = (1-f)/N + f
    # variável: x=1/N, y=1/S → y = (1-f)x + f → intercept=f, slope=(1-f)
    from numpy.polynomial import polynomial as P
    coefs = np.polyfit(inv_n, inv_s, 1)   # coefs[0]=slope, coefs[1]=intercept
    f_est = coefs[1]
    f_est = max(0.0, min(1.0, f_est))

    N_range = np.linspace(1, max(threads), 200)
    speedup_amdahl = 1.0 / (f_est + (1 - f_est) / N_range)
    speedup_ideal  = N_range

    ax.plot(N_range, speedup_ideal, "--", color="gray", linewidth=1.2, label="Speedup ideal (linear)")
    ax.plot(N_range, speedup_amdahl, "-", color="#fdae61", linewidth=2,
            label=f"Lei de Amdahl (f={f_est:.3f})")
    ax.errorbar(threads, speedup, yerr=err_sp,
                fmt="o", color="#2c7bb6", markersize=6, capsize=4,
                linewidth=2, label="Speedup observado (IC 95%)")
    ax.axvline(LIMITE_FISICO, color="#d7191c", linestyle=":", linewidth=1.5,
               label=f"Limite P-cores físicos ({LIMITE_FISICO})")

    ax.set_xlabel("Número de threads")
    ax.set_ylabel("Speedup")
    ax.set_title("Fig. 2 — Speedup observado vs. Lei de Amdahl\n(Multiplicação de matrizes 800×800, i7-13620H)")
    ax.set_xticks(threads)
    ax.legend()
    fig.tight_layout()
    path = GRAF_DIR / "fig2_speedup_amdahl.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Salvo: {path}")


# ── Fig 3 — Bandwidth / Cache ─────────────────────────────────────────────────
def fig3_bandwidth_cache():
    """Lê arquivos mbw_*.txt do dados_piloto (ou dados/raw) e plota barras."""
    import glob

    # Procura arquivos mbw em dados_piloto ou dados/raw
    padroes = [
        str(PILOTO_DIR / "mbw_*.txt"),
        str(RAW_DIR / "mbw_*.txt"),
        str(PILOTO_DIR / "*mbw*"),
        str(RAW_DIR / "*mbw*"),
    ]
    arquivos = []
    for p in padroes:
        arquivos.extend(glob.glob(p))
    arquivos = list(set(arquivos))

    if not arquivos:
        # Gera figura com aviso
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Dados mbw não encontrados.\nRode: mbw -n 5 16 128 1024 > dados_piloto/mbw_resultados.txt",
                ha="center", va="center", fontsize=12, transform=ax.transAxes)
        ax.set_title("Fig. 3 — Largura de banda de memória (dados ausentes)")
        path = GRAF_DIR / "fig3_bandwidth_cache.png"
        fig.savefig(path, dpi=300)
        plt.close(fig)
        print(f"  AVISO: dados mbw não encontrados — figura placeholder salva em {path}")
        return

    # Parseia apenas linhas AVG do mbw
    # Formato: "AVG\tMethod: MEMCPY\tElapsed: ...\tMiB: 16.00\tCopy: 9585.4 MiB/s"
    dados = []
    for arq in arquivos:
        tamanho = re.search(r"(\d+)", os.path.basename(arq))
        tamanho_mib = int(tamanho.group(1)) if tamanho else None
        with open(arq) as f:
            for linha in f:
                if not linha.startswith("AVG"):
                    continue
                m = re.search(r"Method:\s+(\w+).*Copy:\s+([\d.]+)\s+MiB/s", linha)
                if m:
                    dados.append({
                        "metodo": m.group(1),
                        "bandwidth_mbs": float(m.group(2)),
                        "tamanho_mib": tamanho_mib,
                    })

    if not dados:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Não foi possível parsear {arquivos}\nVerifique o formato do arquivo mbw.",
                ha="center", va="center", fontsize=10, transform=ax.transAxes)
        ax.set_title("Fig. 3 — Largura de banda (erro de parsing)")
        path = GRAF_DIR / "fig3_bandwidth_cache.png"
        fig.savefig(path, dpi=300)
        plt.close(fig)
        print(f"  AVISO: parsing mbw falhou — figura placeholder em {path}")
        return

    df = pd.DataFrame(dados)
    fig, ax = plt.subplots(figsize=(10, 6))

    metodos  = df["metodo"].unique()
    tamanhos = sorted([t for t in df["tamanho_mib"].unique() if t is not None])
    if not tamanhos:
        tamanhos = [None]

    x     = np.arange(len(tamanhos))
    width = 0.25
    cores = ["#2c7bb6", "#fdae61", "#d7191c"]

    for i, met in enumerate(metodos[:3]):
        vals = [df[(df["metodo"] == met) & (df["tamanho_mib"] == t)]["bandwidth_mbs"].mean()
                if t is not None else df[df["metodo"] == met]["bandwidth_mbs"].mean()
                for t in tamanhos]
        ax.bar(x + i * width, vals, width, label=met, color=cores[i % len(cores)])

    rotulos = [f"{t} MiB" for t in tamanhos]
    anotacoes = {16: "≤ L2+L3", 128: "~L3", 1024: "→ DRAM"}
    rotulos = [f"{t} MiB\n({anotacoes.get(t,'')})" for t in tamanhos]

    ax.set_xticks(x + width)
    ax.set_xticklabels(rotulos)
    ax.set_xlabel("Tamanho do bloco de memória")
    ax.set_ylabel("Largura de banda (MiB/s)")
    ax.set_title("Fig. 3 — Largura de banda de memória por método e tamanho\n(i7-13620H, mbw)")
    ax.legend()
    fig.tight_layout()
    path = GRAF_DIR / "fig3_bandwidth_cache.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Salvo: {path}")


# ── Fig 4 — Sysbench throughput ───────────────────────────────────────────────
def fig4_sysbench(sys_df):
    fig, ax = plt.subplots(figsize=(10, 6))

    threads = sys_df["n_threads"].values
    eps     = sys_df["media"].values
    err     = ((sys_df["ic95_hi"] - sys_df["ic95_lo"]) / 2).values
    t1_eps  = sys_df.loc[sys_df["n_threads"] == 1, "media"].values[0]
    ideal   = threads * t1_eps

    ax.plot(threads, ideal, "--", color="gray", linewidth=1.2, label="Throughput ideal (N × T₁)")
    ax.errorbar(threads, eps, yerr=err,
                fmt="o-", color="#2c7bb6", linewidth=2, markersize=6,
                capsize=4, label="Throughput observado (IC 95%)")
    ax.axvline(LIMITE_FISICO, color="#d7191c", linestyle=":", linewidth=1.5,
               label=f"Limite P-cores físicos ({LIMITE_FISICO})")

    ax.set_xlabel("Número de threads")
    ax.set_ylabel("Events/s")
    ax.set_title("Fig. 4 — Throughput sysbench CPU por número de threads\n(i7-13620H, --cpu-max-prime=20000)")
    ax.set_xticks(threads)
    ax.legend()
    fig.tight_layout()
    path = GRAF_DIR / "fig4_sysbench_throughput.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Salvo: {path}")


def main():
    print("\n=== Gerando gráficos ===")
    par, sys_df = carregar_resumo()
    fig1_eficiencia(par)
    fig2_speedup_amdahl(par)
    fig3_bandwidth_cache()
    fig4_sysbench(sys_df)
    print("=== Gráficos concluídos ===")


if __name__ == "__main__":
    main()
