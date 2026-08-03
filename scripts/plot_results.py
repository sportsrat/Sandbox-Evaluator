from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'results' / 'raw'
CH = ROOT / 'results' / 'charts'
CH.mkdir(parents=True, exist_ok=True)
PROVIDERS = ['e2b', 'hf', 'docker']
COLOR = {'e2b': '#59a6ff', 'hf': '#ffa05c', 'docker': '#4fc3a1'}
SINCE = float(os.getenv('PLOT_SINCE', '0'))


def load(bench: str, provider: str) -> list[dict]:
    path = RAW / f'{bench}__{provider}.jsonl'
    if not path.exists():
        return []
    rows = []
    for line in path.open():
        row = json.loads(line)
        timestamp = row.get('ts') or (row.get('summary') or {}).get('ts', 0)
        if SINCE and timestamp and timestamp < SINCE:
            continue
        rows.append(row)
    return rows


def plot_b01() -> None:
    fig, axis = plt.subplots(figsize=(8, 4))
    metrics = ['p50', 'p90', 'p99']
    width = 0.8 / len(PROVIDERS)
    x_values = list(range(len(metrics)))
    for index, provider in enumerate(PROVIDERS):
        rows = [row for row in load('b01_boot_latency', provider) if row.get('ok')]
        totals = sorted(row['t_total_ms'] for row in rows)
        values = []
        for metric in metrics:
            if not totals:
                values.append(0)
                continue
            fraction = {'p50': 0.5, 'p90': 0.9, 'p99': 0.99}[metric]
            values.append(totals[int(round(fraction * (len(totals) - 1)))])
        offset = (index - (len(PROVIDERS) - 1) / 2) * width
        bars = axis.bar([x + offset for x in x_values], values, width, label=provider, color=COLOR[provider])
        for bar, value in zip(bars, values):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f'{value:.0f}ms', ha='center', va='bottom', fontsize=9)
    axis.set_xticks(x_values)
    axis.set_xticklabels(metrics)
    axis.set_ylabel('boot to ready (ms)')
    axis.set_title('B01 - Cold boot latency (create + first exec)')
    axis.legend()
    axis.set_yscale('log')
    plt.tight_layout()
    plt.savefig(CH / 'b01_boot_latency.png', dpi=130)
    plt.close()


def plot_b03() -> None:
    sizes = ['1KB', '64KB', '1MB', '10MB']
    fig, (write_axis, read_axis) = plt.subplots(1, 2, figsize=(12, 4.5))
    for provider in PROVIDERS:
        data = load('b03_io_throughput', provider)
        if not data:
            continue
        rows = data[-1]['rows']
        write_axis.plot(sizes, [row['write_mb_per_s'] for row in rows], marker='o', linewidth=2.5, label=provider, color=COLOR[provider])
        read_axis.plot(sizes, [row['read_mb_per_s'] for row in rows], marker='o', linewidth=2.5, label=provider, color=COLOR[provider])
    write_axis.set_ylabel('MB/s')
    write_axis.set_title('B03 - File write throughput')
    write_axis.legend()
    write_axis.grid(True, alpha=0.3)
    read_axis.set_ylabel('MB/s')
    read_axis.set_title('B03 - File read throughput')
    read_axis.legend()
    read_axis.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(CH / 'b03_io.png', dpi=130)
    plt.close()


def plot_b04() -> None:
    counts = [5, 20, 50]
    fig, (rate_axis, latency_axis) = plt.subplots(1, 2, figsize=(12, 4.5))
    for provider in PROVIDERS:
        rows = load('b04_concurrent_create', provider)
        summaries = [row['summary'] for row in rows]
        by_count = {row['n']: row for row in summaries}
        rates = [by_count[count]['success_rate'] * 100 if count in by_count else 0 for count in counts]
        p99s = [by_count[count]['t_ready_ms']['p99'] if count in by_count and by_count[count]['t_ready_ms'].get('p99') else 0 for count in counts]
        rate_axis.plot(counts, rates, marker='o', linewidth=2.5, label=provider, color=COLOR[provider])
        latency_axis.plot(counts, p99s, marker='o', linewidth=2.5, label=provider, color=COLOR[provider])
    rate_axis.set_xlabel('concurrent sandbox count')
    rate_axis.set_ylabel('success rate (%)')
    rate_axis.set_ylim(0, 105)
    rate_axis.legend()
    rate_axis.grid(True, alpha=0.3)
    latency_axis.set_xlabel('concurrent sandbox count')
    latency_axis.set_ylabel('p99 boot to ready (ms)')
    latency_axis.set_yscale('log')
    latency_axis.legend()
    latency_axis.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(CH / 'b04_scaling.png', dpi=130)
    plt.close()


if __name__ == '__main__':
    plot_b01()
    plot_b03()
    plot_b04()
    print('Charts written to', CH)