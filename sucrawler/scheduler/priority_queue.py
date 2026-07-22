import asyncio


class PriorityQueue[T]:
    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue[tuple[int, int, T]] = asyncio.PriorityQueue()
        self._counter: int = 0

    async def push(self, item: T, priority: int = 0) -> None:
        self._counter += 1
        await self._queue.put((priority, self._counter, item))

    async def pop(self) -> T:
        _, _, item = await self._queue.get()
        return item

    def empty(self) -> bool:
        return self._queue.empty()

    def size(self) -> int:
        return self._queue.qsize()
