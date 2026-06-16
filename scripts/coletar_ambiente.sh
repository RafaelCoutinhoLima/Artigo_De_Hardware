#!/usr/bin/env bash
# Captura o ambiente de execucao para reprodutibilidade.
# Uso: bash scripts/coletar_ambiente.sh > dados/raw/ambiente.txt
set -euo pipefail

echo "=== AMBIENTE DO EXPERIMENTO ==="
echo "Data: $(date)"
echo
echo "=== SISTEMA OPERACIONAL ==="
uname -a
lsb_release -a 2>/dev/null
echo
echo "=== CPU ==="
lscpu
echo
echo "=== MEMORIA ==="
free -h
echo
echo "=== STORAGE ==="
lsblk -o NAME,SIZE,TYPE,ROTA,TRAN
echo
echo "=== CPU GOVERNOR ==="
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  echo "$f: $(cat "$f")"
done
echo
echo "=== FREQUENCIAS ATUAIS ==="
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
  echo "$f: $(cat "$f") kHz"
done
echo
echo "=== FERRAMENTAS ==="
sysbench --version 2>/dev/null || true
stress-ng --version 2>/dev/null || true
fio --version 2>/dev/null || true
python3 --version 2>/dev/null || true
