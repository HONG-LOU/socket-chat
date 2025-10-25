import asyncio
import threading
from typing import Optional


class AsyncioRunner:
    _instance: Optional["AsyncioRunner"] = None

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    @classmethod
    def instance(cls) -> "AsyncioRunner":
        if cls._instance is None:
            cls._instance = AsyncioRunner()
        return cls._instance

    def start(self) -> None:
        if self._loop and self._loop.is_running():
            return

        def _run() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            loop.run_forever()

        self._thread = threading.Thread(target=_run, name="asyncio-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def create_task(self, coro: "asyncio.coroutines.Coroutine"):
        if not self._loop:
            raise RuntimeError("AsyncioRunner not started")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
