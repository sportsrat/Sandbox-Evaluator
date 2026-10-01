# E2B vs Docker Sandbox Benchmark Report

**Date:** 2026-10-01  
**Fresh providers:** E2B and Docker  
**Historical reference:** Hugging Face values are retained from the previous report and were not rerun.

## Executive summary

This report reruns the provider-neutral sandbox tests that work directly through the local adapter interface. No MCP server, MCP tool, or MCP-specific transport was used.

| Dimension | E2B | Docker | Result |
|---|---:|---:|---|
| Cold boot to first command, p50 | 906 ms | 625 ms | Docker |
| Warm exec throughput | 3.44 ops/s | 12.07 ops/s | Docker |
| Warm exec latency, p50 | 266 ms | 78 ms | Docker |
| 10 MB write | 2.79 MB/s | 20.36 MB/s | Docker |
| 10 MB read | 22.36 MB/s | 83.89 MB/s | Docker |
| Concurrent create, N=20 | 20/20, 3.5 s | 20/20, 10.2 s | E2B |
| Concurrent create, N=50 | 20/50, quota | 50/50, 14.1 s | Docker |
| Concurrent exec, N=10 | 200/200 | 200/200 | Tie |
| Five-minute stability | 15/15 | 15/15 | Tie |
| Max-provision ramp | Quota at N=50 | 50/50 at N=50 | Docker in this run |

### Bottom line

Docker was faster for every latency, throughput, and file-transfer measurement in this run. E2B created 20 sandboxes faster than Docker and remained healthy at N=20, but the E2B account returned quota errors during the N=50 tests. Docker successfully held 50 concurrent sandboxes on the local Docker Desktop engine.

These results are directional: Docker runs on the local machine and its result depends on host CPU, memory, storage, and Docker Desktop configuration. E2B is a remote managed service and its result depends on region, account limits, image cache state, and network conditions.

## Methodology

All tests used the same adapter operations: `create`, `exec`, `write`, `read`, and `terminate`. The fresh result window began at Unix timestamp `1790876800`. Raw JSONL measurements are in `results/raw/`; charts are in `results/charts/`.

- **B01:** five fresh create plus `echo ready` lifecycles.
- **B02:** 100 sequential `echo x` operations in one sandbox.
- **B03:** three write/read repetitions at 1 KB, 64 KB, 1 MB, and 10 MB.
- **B04:** concurrent create plus first command at N=5, 20, and 50.
- **B05:** ten sandboxes, 20 sequential commands per sandbox.
- **B06:** one sandbox, 15 pings over five minutes at 20-second intervals.
- **B07:** concurrent held-sandbox ramp at N=5, 20, and 50; stop on quota or below-90% success.

## Detailed fresh results

### B01: Cold boot

| Provider | Successful runs | Create range | Boot to ready p50 |
|---|---:|---:|---:|
| E2B | 5/5 | 391-2,016 ms | 906 ms |
| Docker | 5/5 | 484-922 ms | 625 ms |

E2B had one slower first run, while Docker was more consistent in this sample.

### B02: Warm execution

| Provider | Successful commands | Throughput | Exec p50 |
|---|---:|---:|---:|
| E2B | 100/100 | 3.44 ops/s | 266 ms |
| Docker | 100/100 | 12.07 ops/s | 78 ms |

Docker avoids the remote request and sandbox-service latency, so this advantage is expected and should not be interpreted as a managed-service comparison.

### B03: File I/O

| Provider | 10 MB write | 10 MB read |
|---|---:|---:|
| E2B | 2.79 MB/s | 22.36 MB/s |
| Docker | 20.36 MB/s | 83.89 MB/s |

All Docker payload checks passed. E2B reported successful 10 MB readback, but some smaller write repetitions were not retained as successful measurements by the adapter run; the raw row is preserved without replacement.

### B04: Concurrent create

| N | E2B | Docker |
|---:|---:|---:|
| 5 | 5/5, 2.7 s | 5/5, 6.9 s |
| 20 | 20/20, 3.5 s | 20/20, 10.2 s |
| 50 | 20/50, 3.8 s, quota errors | 50/50, 14.1 s |

### B05: Concurrent execution

| Provider | Sandboxes | Operations | Wall time | Worker p50 of p50 | Worst worker p99 |
|---|---:|---:|---:|---:|---:|
| E2B | 10/10 | 200/200 | 9.2 s | 266 ms | 1,140 ms |
| Docker | 10/10 | 200/200 | 11.4 s | 109 ms | 2,093 ms |

### B06: Five-minute stability

| Provider | Successful pings | Survival rate |
|---|---:|---:|
| E2B | 15/15 | 100% |
| Docker | 15/15 | 100% |

### B07: Maximum provision ramp

| Provider | N=5 | N=20 | N=50 |
|---|---:|---:|---:|
| E2B | 5/5 | 20/20 | 20/50, quota at 30 creates |
| Docker | 5/5 | 20/20 | 50/50 |

The E2B N=50 result is an account quota observation, not evidence that the E2B service cannot scale to 50. A higher-quota account or a later run is needed to measure that ceiling.

## Historical Hugging Face reference

These values are copied from the previous report and intentionally left intact; no Hugging Face calls were made in this refresh because the account has no pre-paid Jobs credit.

| Dimension | Historical HF value |
|---|---:|
| Cold boot to ready p50 | 15,965 ms |
| Warm exec throughput | 8.4 ops/s |
| Warm exec p50 | 116 ms |
| 10 MB write | 10.05 MB/s |
| 10 MB read | 4.30 MB/s |
| Concurrent create N=20 | 20/20 |
| Concurrent create N=50 | 50/50, 191 s |
| Concurrent exec N=10 | 10/10 |
| Five-minute stability | 15/15 |

The historical HF figures are not directly same-day measurements with the fresh E2B/Docker rows. They are included for continuity only.

## Reproduction commands

Activate the project environment first:

```powershell
.venv\Scripts\Activate.ps1
```

Then run the benchmarks with the provider flag, for example:

```powershell
python benchmarks\b01_boot_latency.py --provider e2b --n 5
python benchmarks\b01_boot_latency.py --provider docker --n 5
python benchmarks\b02_exec_throughput.py --provider e2b
python benchmarks\b02_exec_throughput.py --provider docker
```

Regenerate charts and the self-contained HTML report with:

```powershell
python scripts\plot_results.py
python scripts\build_html_report.py
```
