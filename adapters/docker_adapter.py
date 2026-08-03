from __future__ import annotations

import io
import atexit
import os
import tarfile
import threading
import time
from pathlib import PurePosixPath

from .base import SandboxAdapter


class DockerAdapter(SandboxAdapter):
    name = 'docker'
    cost_per_sandbox_sec = 0.0
    cost_notes = 'Local Docker Engine; excludes host and Docker Desktop costs'

    def __init__(self) -> None:
        super().__init__()
        atexit.register(self.terminate)

    def _do_create(self, *, image: str, **kwargs):
        import docker

        self._client = docker.from_env()
        if image == 'python:3.12-slim':
            image = os.getenv('DOCKER_IMAGE', image)
        self._image = image
        network_enabled = kwargs.get('network_enabled', _env_bool('DOCKER_NETWORK_ENABLED', True))
        options = {
            'detach': True,
            'command': ['sh', '-c', 'while :; do sleep 3600; done'],
            'remove': False,
            'network_disabled': not network_enabled,
        }
        cpu_limit = kwargs.get('cpu_limit') or os.getenv('DOCKER_CPU_LIMIT') or None
        memory_limit = kwargs.get('memory_limit') or os.getenv('DOCKER_MEMORY_LIMIT') or None
        pids_limit = kwargs.get('pids_limit', _env_int('DOCKER_PIDS_LIMIT'))
        if cpu_limit is not None:
            options['nano_cpus'] = int(float(cpu_limit) * 1_000_000_000)
        if memory_limit is not None:
            options['mem_limit'] = memory_limit
        if pids_limit is not None:
            options['pids_limit'] = int(pids_limit)
        self.handle = self._client.containers.run(self._image, **options)
        self._created_at = time.monotonic()
        return self.handle

    def _do_exec(self, *, cmd, timeout: float):
        command = cmd if isinstance(cmd, list) else ['sh', '-c', cmd]
        result: list[object] = []
        failure: list[BaseException] = []

        def run() -> None:
            try:
                result.append(self.handle.exec_run(command, demux=True))
            except BaseException as exc:
                failure.append(exc)

        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            try:
                self.handle.kill()
            finally:
                raise TimeoutError(f'Docker command timed out after {timeout}s')
        if failure:
            raise failure[0]

        exec_result = result[0]
        output = exec_result.output
        if isinstance(output, tuple):
            stdout, stderr = output
        else:
            stdout, stderr = output, b''
        return {
            'rc': exec_result.exit_code,
            'stdout': _decode(stdout),
            'stderr': _decode(stderr),
        }

    def _do_write(self, *, path: str, content):
        target = PurePosixPath(path)
        if not target.is_absolute() or target.name in ('', '.', '..'):
            raise ValueError(f'path must name an absolute file: {path!r}')
        data = content.encode() if isinstance(content, str) else bytes(content)
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode='w') as tar:
            info = tarfile.TarInfo(target.name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        self.handle.put_archive(str(target.parent), archive.getvalue())
        return None

    def _do_read(self, *, path: str):
        stream, _ = self.handle.get_archive(path)
        data = b''.join(stream)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as tar:
            member = next((item for item in tar.getmembers() if item.isfile()), None)
            if member is None:
                raise FileNotFoundError(path)
            extracted = tar.extractfile(member)
            if extracted is None:
                raise FileNotFoundError(path)
            return extracted.read()

    def _do_terminate(self):
        if self.handle is None:
            return None
        try:
            self.handle.stop(timeout=5)
        finally:
            try:
                self.handle.remove(force=True)
            finally:
                self.handle = None
        return None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() not in {'0', 'false', 'no', 'off'}


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None


def _decode(value) -> str:
    if value is None:
        return ''
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else str(value)