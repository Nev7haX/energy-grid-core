"""Realtime telemetry ingestion and batch flushing."""

from __future__ import annotations

import asyncio

from app.core.exceptions import BackpressureError
from app.core.logging import get_logger

from .connector_interfaces import TelemetrySample
from .history_storage import HistoryStoragePort
from .state_manager import DeviceStateManager

LOGGER = get_logger(__name__)


class RealtimeStreamProcessor:
    """Queue-based realtime telemetry processor with batch flushing."""

    def __init__(
        self,
        *,
        history_storage: HistoryStoragePort,
        state_manager: DeviceStateManager,
        queue_maxsize: int,
        batch_size: int,
        flush_interval_seconds: float,
    ) -> None:
        """Initialize the realtime processor.

        Args:
            history_storage: Historical storage implementation.
            state_manager: Latest state manager.
            queue_maxsize: Maximum buffered telemetry events.
            batch_size: Maximum batch size per flush.
            flush_interval_seconds: Maximum flush interval.

        Returns:
            None.
        """
        self._history_storage = history_storage
        self._state_manager = state_manager
        self._queue: asyncio.Queue[TelemetrySample] = asyncio.Queue(maxsize=queue_maxsize)
        self._batch_size = batch_size
        self._flush_interval_seconds = flush_interval_seconds
        self._stop_event = asyncio.Event()
        self._worker_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the background worker if not already running.

        Args:
            None.

        Returns:
            None.
        """
        if self._worker_task is None:
            self._stop_event.clear()
            self._worker_task = asyncio.create_task(self._run(), name="telemetry-stream-processor")

    async def stop(self) -> None:
        """Stop the background worker and flush remaining telemetry.

        Args:
            None.

        Returns:
            None.
        """
        if self._worker_task is None:
            return

        self._stop_event.set()
        await self._worker_task
        self._worker_task = None

    async def submit(self, sample: TelemetrySample) -> None:
        """Submit a telemetry sample to the ingestion queue.

        Args:
            sample: Normalized telemetry sample.

        Returns:
            None.

        Raises:
            BackpressureError: If the queue is full.
        """
        try:
            self._queue.put_nowait(sample)
        except asyncio.QueueFull as exc:
            raise BackpressureError(
                "Telemetry buffer is full. Slow down producers or increase queue capacity."
            ) from exc

    async def _run(self) -> None:
        """Run the background telemetry drain loop.

        Args:
            None.

        Returns:
            None.
        """
        batch: list[TelemetrySample] = []

        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                item = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._flush_interval_seconds,
                )
                batch.append(item)
                if len(batch) >= self._batch_size:
                    await self._flush_batch(batch)
                    self._acknowledge_batch(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    self._acknowledge_batch(batch)
                    batch = []

        if batch:
            await self._flush_batch(batch)
            self._acknowledge_batch(batch)

    async def _flush_batch(self, batch: list[TelemetrySample]) -> None:
        """Flush a telemetry batch to state and history stores.

        Args:
            batch: Buffered telemetry batch.

        Returns:
            None.
        """
        if not batch:
            return

        # 先批量更新最新态，再统一写入历史存储，避免高频单条写入造成锁竞争。
        await self._state_manager.update_from_records(batch)
        await self._history_storage.append_records(batch)
        LOGGER.debug("Flushed %s telemetry records.", len(batch))

    def _acknowledge_batch(self, batch: list[TelemetrySample]) -> None:
        """Mark flushed queue items as completed.

        Args:
            batch: Flushed telemetry batch.

        Returns:
            None.
        """
        for _ in batch:
            self._queue.task_done()

    async def drain(self) -> None:
        """Force the processor to flush currently queued events.

        Args:
            None.

        Returns:
            None.
        """
        await self._queue.join()
