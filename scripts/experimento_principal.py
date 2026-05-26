#!/usr/bin/env python3
# Fase 1 — Experimento Principal
# Coleta dados de paralelismo (matrix mul) e sysbench CPU para o artigo.
# Python: /home/rafael-coutinho/venv/bin/python

import csv
import subprocess
import time
import re
import os
import multiprocessing
from multiprocessing import Pool

# ── Configurações ──────────────────────────────────────────────────────────────
THREADS_LISTA = [1, 2, 4, 6, 8, 10, 12, 14, 16]
N_WARMUP      = 3
N_MEDICOES    = 30
MATRIX_SIZE   = 800
SYSBENCH_TIME = 10
PRIME_MAX     = 20000
SLEEP_ENTRE_BLOCOS = 2  # segundos entre blocos de threads

RAW_DIR  = os.path.join(os.path.dirname(__file__), "..", "dados", "raw")
CSV_PAR  = os.path.join(RAW_DIR, "paralelismo_raw.csv")
CSV_SYS  = os.path.join(RAW_DIR, "sysbench_raw.csv")


# ── Tarefa de multiplicação de matrizes ────────────────────────────────────────
def _multiplicar_matrizes(_):
    """Cada processo faz uma multiplicação 800×800 independente."""
    import numpy as np
    rng = np.random.default_rng()
    A = rng.random((MATRIX_SIZE, MATRIX_SIZE))
    B = rng.random((MATRIX_SIZE, MATRIX_SIZE))
    _ = A @ B


def medir_paralelismo(n_threads: int) -> float:
    """Retorna o tempo (s) para executar n_threads multiplicações em paralelo."""
    inicio = time.perf_counter()
    with Pool(processes=n_threads) as pool:
        pool.map(_multiplicar_matrizes, range(n_threads))
    return time.perf_counter() - inicio


# ── Tarefa sysbench ────────────────────────────────────────────────────────────
def medir_sysbench(n_threads: int) -> float:
    """Retorna events/s reportado pelo sysbench."""
    cmd = [
        "sysbench", "cpu",
        f"--cpu-max-prime={PRIME_MAX}",
        f"--threads={n_threads}",
        f"--time={SYSBENCH_TIME}",
        "run"
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    # Extrai "events per second: XXXXXX"
    match = re.search(r"events per second:\s+([\d.]+)", resultado.stdout)
    if not match:
        raise RuntimeError(f"sysbench não retornou eventos/s:\n{resultado.stdout}")
    return float(match.group(1))


# ── Loop principal ─────────────────────────────────────────────────────────────
def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    with open(CSV_PAR, "w", newline="") as f_par, \
         open(CSV_SYS, "w", newline="") as f_sys:

        writer_par = csv.writer(f_par)
        writer_sys = csv.writer(f_sys)
        writer_par.writerow(["n_threads", "repeticao", "tempo_s"])
        writer_sys.writerow(["n_threads", "repeticao", "events_per_sec"])

        for n in THREADS_LISTA:
            print(f"\n{'='*60}")
            print(f"  Threads: {n}  |  warmup={N_WARMUP}  medicoes={N_MEDICOES}")
            print(f"{'='*60}")

            # Aquecimento — descartado
            print(f"  [warmup] ", end="", flush=True)
            for w in range(N_WARMUP):
                medir_paralelismo(n)
                medir_sysbench(n)
                print(f"w{w+1} ", end="", flush=True)
            print()

            # Medições oficiais
            for rep in range(1, N_MEDICOES + 1):
                # (A) Paralelismo
                t = medir_paralelismo(n)
                writer_par.writerow([n, rep, f"{t:.6f}"])
                f_par.flush()

                # (B) Sysbench
                eps = medir_sysbench(n)
                writer_sys.writerow([n, rep, f"{eps:.3f}"])
                f_sys.flush()

                print(f"  rep {rep:02d}/{N_MEDICOES}  paralelismo={t:.3f}s  sysbench={eps:.1f} ev/s")

            print(f"  Dormindo {SLEEP_ENTRE_BLOCOS}s para esfriar CPU...")
            time.sleep(SLEEP_ENTRE_BLOCOS)

    print(f"\n{'='*60}")
    print(f"  Experimento concluído!")
    print(f"  → {CSV_PAR}")
    print(f"  → {CSV_SYS}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Garante que o multiprocessing funciona corretamente no Linux
    multiprocessing.set_start_method("spawn", force=True)
    main()
