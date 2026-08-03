from .base import SandboxAdapter, AdapterError, OpResult
from .e2b_adapter import E2BAdapter
from .hf_adapter import HFAdapter
from .docker_adapter import DockerAdapter

ADAPTERS: dict[str, type[SandboxAdapter]] = {
	'e2b': E2BAdapter,
	'hf': HFAdapter,
	'docker': DockerAdapter,
}
__all__ = ['SandboxAdapter', 'AdapterError', 'OpResult', 'E2BAdapter', 'HFAdapter', 'DockerAdapter', 'ADAPTERS']
