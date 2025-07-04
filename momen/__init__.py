from momen.debugger import Debugger
from typing import Union


def process(target: Union[int, str]) -> Debugger:
    dbg = Debugger()
    match target:
        case str():
            dbg.load_executable(target)
        case int():
            dbg.attach(target)
        case _:
            raise TypeError("target must be a file path or pid")
    return dbg
