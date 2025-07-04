import os
import select


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

    def recv(self, size: int = 4096) -> bytes:
        if self._buf:
            data = self._buf[:size]
            self._buf = self._buf[size:]
            return data

        rlist, _, _ = select.select([self._fd], [], [], 0.1)
        if not rlist:
            return b""

        data = os.read(self._fd, size)

        self._buf = data[size:]
        return data[:size]

    def recvuntil(self, delim: bytes, drop: bool = False) -> bytes:
        data = b""
        pos = 0
        while True:
            data += self.recv()
            if (pos := data.find(delim)) != -1:
                break

        if drop:
            self._buf = data[pos:]
            return data[:pos]
        else:
            self._buf = data[pos + len(delim) :]
            return data[: pos + len(delim)]

    def recvline(self) -> bytes:
        return self.recvuntil(b"\n")

    def read(self, size: int) -> bytes:
        return self.recv(size)

    def readuntil(self, delim: bytes) -> bytes:
        return self.recvuntil(delim)

    def readline(self) -> bytes:
        return self.recvline()
