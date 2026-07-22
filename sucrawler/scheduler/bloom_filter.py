import hashlib
import math
from collections.abc import Sequence


class BloomFilter:
    def __init__(self, capacity: int, error_rate: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if not 0 < error_rate < 1:
            raise ValueError("error_rate must be between 0 and 1")

        self.capacity = capacity
        self.error_rate = error_rate
        self._size = self._calculate_size(capacity, error_rate)
        self._hash_count = self._calculate_hash_count(self._size, capacity)
        self._bit_array: set[int] = set()

    @staticmethod
    def _calculate_size(capacity: int, error_rate: float) -> int:
        size = -(capacity * math.log(error_rate)) / (math.log(2) ** 2)
        return max(1, int(size))

    @staticmethod
    def _calculate_hash_count(size: int, capacity: int) -> int:
        count = (size / capacity) * math.log(2)
        return max(1, int(count))

    def _get_hashes(self, item: str) -> Sequence[int]:
        hashes: list[int] = []
        for i in range(self._hash_count):
            data = f"{i}:{item}".encode()
            hash_value = int(hashlib.sha256(data).hexdigest(), 16)
            hashes.append(hash_value % self._size)
        return hashes

    def add(self, item: str) -> None:
        for position in self._get_hashes(item):
            self._bit_array.add(position)

    def contains(self, item: str) -> bool:
        return all(position in self._bit_array for position in self._get_hashes(item))
