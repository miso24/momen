import os
import select
import time


DEFAULT_TIMEOUT = 10


class InferiorIO:
    def __init__(self, fd: int) -> None:
        self._fd = fd
        self._buf = bytearray()

    def send(self, data: bytes) -> int:
        return os.write(self._fd, data)

    def sendline(self, data: bytes) -> int:
        return os.write(self._fd, data + b"\n")

    def sendafter(self, delim: bytes, data: bytes) -> int:
        self.recvuntil(delim)
        return self.send(data)

    def sendlineafter(self, delim: bytes, data: bytes) -> int:
        self.recvuntil(delim)
        return self.sendline(data)

    def recv(self, size: int = 4096, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        if self._buf:
            data = self._buf[:size]
            self._buf = self._buf[size:]
            return data

        rlist, _, _ = select.select([self._fd], [], [], timeout)
        if not rlist:
            return b""

        data = os.read(self._fd, size)

        self._buf = data[size:]
        return data[:size]

    def recvuntil(
        self, delim: bytes, drop: bool = False, timeout: float = DEFAULT_TIMEOUT
    ) -> bytes:
        data = b""
        end_time = time.time() + timeout
        while True:
            remain = end_time - time.time()
            if remain < 0:
                raise TimeoutError("timeout")
            data += self.recv(timeout=remain)
            if (pos := data.find(delim)) != -1:
                break

        if drop:
            self._buf = data[pos:]
            return data[:pos]
        else:
            self._buf = data[pos + len(delim) :]
            return data[: pos + len(delim)]

    def recvline(self, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        return self.recvuntil(b"\n", timeout=timeout)

    def read(self, size: int, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        return self.recv(size, timeout=timeout)

    def readuntil(self, delim: bytes, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        return self.recvuntil(delim, timeout=timeout)

    def readline(self, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        return self.recvline(timeout=timeout)
