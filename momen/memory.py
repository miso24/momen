from momen.gdbmi.controller import GdbController
from typing import Union


class Memory:
    def __init__(self, controller: GdbController) -> None:
        self.controller = controller

    def read(self, address: int, size: int) -> bytes:
        result = self.controller.exec_command(
            f"-data-read-memory-bytes {address} {size}"
        )
        if not result:
            return b""
        if result.is_error():
            return b""

        mem_info = result.payload["memory"]
        contents = bytes.fromhex(mem_info[0]["contents"])  # type: ignore
        return contents

    def write(self, address: int, data: bytes) -> None:
        self.controller.exec_command(f"-data-write-memory-bytes {address} {data.hex()}")

    def __getitem__(self, key: Union[int, slice, tuple]) -> bytes:
        match key:
            case int():
                return self.read(key, 1)
            case slice():
                start = key.start or 0
                stop = key.stop or start
                if start > stop:
                    raise ValueError("Slice stop must be >= start")
                size = stop - start
                return self.read(start, size)
            case tuple():
                if len(key) != 2:
                    raise ValueError("Tuple index must be (addr, size)")

                addr, size = key
                if not isinstance(addr, int) or not isinstance(size, int):
                    raise TypeError("Both address and size must be int")
                if size < 0:
                    raise ValueError("Size must be non negative")
                return self.read(addr, size)
            case _:
                raise TypeError("Memory access must be int, slice, or (addr, size)")

    def __setitem__(self, key: Union[int, slice, tuple], value: Union[int, bytes]):
        match key:
            case int():
                if isinstance(value, int):
                    data = bytes([value])
                else:
                    data = value
                return self.write(key, data)
            case slice():
                if not isinstance(value, bytes):
                    raise TypeError("Expected bytes for slice write")
                start = key.start or 0
                stop = key.stop or start
                size = stop - start
                if start > stop:
                    raise ValueError("Slice stop must be >= start")
                if len(value) != size:
                    raise ValueError(
                        f"Size mismatch: expected {size}, got {len(value)}"
                    )
                return self.read(start, size)
            case tuple():
                if len(key) != 2:
                    raise ValueError("Tuple index must be (addr, size)")

                addr, size = key
                if not isinstance(addr, int) or not isinstance(size, int):
                    raise TypeError("Both address and size must be int")
                if size < 0:
                    raise ValueError("Size must be non negative")
                if not isinstance(value, bytes):
                    raise TypeError("Expected bytes for tuple write")
                if len(value) != size:
                    raise ValueError(
                        f"Size mismatch: expected {size}, got {len(value)}"
                    )
                return self.read(addr, size)
            case _:
                raise TypeError("Memory access must be int, slice, or (addr, size)")
