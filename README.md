# Evaluating Sandboxes

Provider-agnostic benchmarking for AI code-execution sandboxes:

- **E2B** - managed remote sandbox
- **Hugging Face Jobs** - managed remote sandbox
- **Docker** - local Docker Engine container

All three providers use the same `SandboxAdapter` interface:
`create()`, `exec()`, `write()`, `read()`, and `terminate()`.

Docker is the sandbox in the local implementation. An AI agent, if added later,
would remain outside the container and send code or commands through the adapter.
Docker container isolation is not equivalent to a managed remote sandbox or a
stronger microVM or gVisor-style security boundary.


For example:

```text
LLM / Agent
     |
     v
Code Execution Request
     |
     v
+-----------------------------+
|      Sandbox Interface      |
+-----------------------------+
      |       |        |
      v       v        v
     E2B      HF     Docker
   Remote   Remote    Local
   Sandbox  Sandbox  Container


```

```text
adapters/
  base.py
  e2b_adapter.py
  hf_adapter.py
  docker_adapter.py
benchmarks/
  b01_boot_latency.py
  b02_exec_throughput.py
  b03_io_throughput.py
  b04_concurrent_create.py
  b05_concurrent_exec.py
  b06_long_running.py
  b07_max_provision.py
scripts/
  verify_setup.py
  plot_results.py
  summarize.py
  build_html_report.py
results/raw/
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

Set `E2B_API_KEY` and `HF_TOKEN` for the remote providers. Docker requires
Docker Engine or Docker Desktop to be running and uses no cloud token.

Docker configuration is optional and is read from `.env`:

- `DOCKER_IMAGE` (default `python:3.12-slim`)
- `DOCKER_NETWORK_ENABLED`
- `DOCKER_CPU_LIMIT`
- `DOCKER_MEMORY_LIMIT`
- `DOCKER_PIDS_LIMIT`

Docker pulls the configured image automatically on the first container creation
when it is not already cached locally.

## Verification

Run the adapter smoke test:

```powershell
python scripts/verify_setup.py
```

It tests create, command execution, file write, file read, termination, and
prints a PASS/FAIL verdict for `e2b`, `hf`, and `docker`. Missing remote
credentials retain the existing skip behavior.

## Benchmarks

The same benchmark code accepts any retained provider:

```powershell
python benchmarks/b01_boot_latency.py --provider docker --n 5
python benchmarks/b01_boot_latency.py --provider e2b --n 5
python benchmarks/b01_boot_latency.py --provider hf --n 5
python benchmarks/b02_exec_throughput.py --provider docker
python benchmarks/b03_io_throughput.py --provider docker
python benchmarks/b04_concurrent_create.py --provider docker --n 20
python benchmarks/b05_concurrent_exec.py --provider docker --n 10
python benchmarks/b06_long_running.py --provider docker
python benchmarks/b07_max_provision.py --provider docker --rungs 5,20,50
```

Raw JSONL results are written under `results/raw/` by benchmark and provider.
Charts can be generated with:

```powershell
python scripts/plot_results.py
python scripts/summarize.py
python scripts/build_html_report.py
```
<img width="1171" height="842" alt="image" src="https://github.com/user-attachments/assets/5e9ed84f-0ff7-4dbc-89a1-05ef50d134f8" />


Benchmark results are measurements from the current machine and provider
accounts. Failed runs remain visible in the raw results and are not replaced by
fabricated values.
