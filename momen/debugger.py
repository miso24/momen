from momen.gdbmi.controller import GdbController
from momen.inferior_io import InferiorIO
from momen.memory import Memory
import pty
import os


class Debugger:
    def __init__(self) -> None:
        self._controller = GdbController()
        self.memory = Memory(self._controller)

    def run(self, args: list[str] = []) -> InferiorIO:
        master_fd, slave_fd = pty.openpty()
        slave_name = os.ttyname(slave_fd)
        self._controller.exec_command(f"-inferior-tty-set {slave_name}")
        if args:
            self._controller.exec_command(f"-exec-arguments {' '.join(args)}")
        self._controller.exec_command("-exec-run")
        os.close(slave_fd)
        return InferiorIO(master_fd)

    def attach(self, pid: int):
        result = self._controller.exec_command(f"-target-attach {pid}")
        if result and result.is_error():
            raise RuntimeError(
                f"Failed to attach to PID {pid}: {result.payload['msg']}"
            )

    def load_executable(self, path: str):
        result = self._controller.exec_command(f"-file-exec-and-symbols {path}")
        if result and result.is_error():
            raise RuntimeError(
                f"Failed to load executable {path}: {result.payload['msg']}"
            )
