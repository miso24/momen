import subprocess
import select
import threading
import os
import time
from queue import Queue, Empty
from typing import Optional, Callable

from momen.gdbmi.parser import parse_record
from momen.gdbmi.record import AsyncRecord, RecordType, ResultRecord

AsyncCallback = Callable[[AsyncRecord], None]
AsyncCallbackMap = dict[str, AsyncCallback]


class GdbController:
    def __init__(self):
        self.gdb = subprocess.Popen(
            ["gdb", "--interpreter=mi2", "-q"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0,
        )

        self._event_queue = Queue()
        self._output_queue = Queue()
        self._async_callbacks: AsyncCallbackMap = {}

        if self.gdb.stdout is None:
            raise RuntimeError("Failed to open gdb stdout")
        if self.gdb.stdin is None:
            raise RuntimeError("Failed to open gdb stdin")

        self.stdout_fd = self.gdb.stdout.fileno()
        self._poll_thread = threading.Thread(target=self._poll_event, daemon=True)
        self._evelt_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._poll_thread.start()
        self._evelt_thread.start()

    def _poll_event(self) -> None:
        while True:
            rlist, _, _ = select.select([self.stdout_fd], [], [], 0.1)
            if self.stdout_fd not in rlist:
                continue

            data = os.read(self.stdout_fd, 4096)
            if not data:
                break

            lines = data.decode().splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                record = parse_record(line)
                if record is None:
                    continue
                if record.type == RecordType.ASYNC:
                    self._event_queue.put(record)
                else:
                    self._output_queue.put(record)

    def _event_loop(self) -> None:
        while True:
            try:
                record = self._event_queue.get(block=True)
                self._handle_async_event(record)
            except Empty:
                continue

    def _handle_async_event(self, record: AsyncRecord):
        if record.async_class in self._async_callbacks:
            callback = self._async_callbacks[record.async_class]
            callback(record)

    def send_command(self, command: str) -> None:
        if self.gdb.stdin is None:
            raise RuntimeError("GDB stdin is not available")
        self.gdb.stdin.write((command + "\n").encode())
        self.gdb.stdin.flush()

    def exec_command(self, command: str, timeout=5) -> Optional[ResultRecord]:
        self.send_command(command)
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                record = self._output_queue.get(timeout=1)
                if record.type != RecordType.RESULT:
                    continue
                return record
            except Empty:
                continue

    def register_async_callback(
        self, async_class: str, callback: AsyncCallback
    ) -> None:
        self._async_callbacks[async_class] = callback
