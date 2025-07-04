import re
from typing import Optional
from momen.gdbmi.record import (
    Payload,
    PayloadValue,
    Record,
    AsyncRecord,
    ResultRecord,
    StreamRecord,
    PromptRecord,
    StreamType,
)

RESULT_RECORD_PATTERN = re.compile(r"^\^(.+?)(?:,(.*))?$")
ASYNC_RECORD_PATTERN = re.compile(r"^[+*=](.+?)(?:,(.*))?$")


def split_fields(s: str) -> list[str]:
    raw_results = []
    bracket_stack = []
    quote_stack = []
    start, pos = 0, 0
    while pos < len(s):
        ch = s[pos]
        match ch:
            case "[" | "{":
                bracket_stack.append(ch)
            case "]":
                if bracket_stack and bracket_stack[-1] != "[":
                    raise ValueError(
                        "Mismatched closing bracket ']' at position {}".format(pos)
                    )
                bracket_stack.pop()
            case "}":
                if bracket_stack and bracket_stack[-1] != "{":
                    raise ValueError(
                        "Mismatched closing bracket '}}' at position {}".format(pos)
                    )
                bracket_stack.pop()
            case '"':
                if quote_stack and quote_stack[-1] == '"':
                    quote_stack.pop()
                else:
                    quote_stack.append('"')
            case ",":
                if not bracket_stack and not quote_stack:
                    raw_results.append(s[start:pos])
                    start = pos + 1
        pos += 1

    if start < len(s):
        raw_results.append(s[start:])
    return raw_results


def parse_list(s: str) -> PayloadValue:
    fields = split_fields(s)

    def is_result(field: str) -> bool:
        return "=" in field and not field.startswith(("{", "["))

    if all(is_result(f) for f in fields):
        return [parse_tuple(field) for field in fields]
    elif all(not is_result(f) for f in fields):
        return [parse_value(field) for field in fields]
    else:
        raise ValueError("Mixed types in list: {}".format(s))


def parse_value(s: str) -> PayloadValue:
    if s.startswith("{") and s.endswith("}"):
        return parse_tuple(s[1:-1])
    elif s.startswith("[") and s.endswith("]"):
        return parse_list(s[1:-1])
    elif s.startswith('"') and s.endswith('"'):
        return s.strip('"')
    else:
        raise ValueError(f"Invalid value format: {s}")


def parse_tuple(s: str) -> Payload:
    fields = split_fields(s)
    result = {}
    for f in fields:
        var, value = parse_key_value(f)
        result[var] = value
    return result


def parse_key_value(s: str) -> tuple[str, PayloadValue]:
    var, value = s.split("=", 1)
    return var, parse_value(value)


def parse_result(s: str) -> Payload:
    return parse_tuple(s)


def parse_result_record(s: str) -> Optional[ResultRecord]:
    m = RESULT_RECORD_PATTERN.match(s)
    if m is None:
        return None
    result_class, rest = m.groups()
    payload = parse_result(rest) if rest is not None else {}
    return ResultRecord(result_class, payload)


def parse_async_record(s: str) -> Optional[AsyncRecord]:
    m = ASYNC_RECORD_PATTERN.match(s)
    if m is None:
        return None
    async_class, rest = m.groups()
    payload = parse_result(rest) if rest is not None else {}
    return AsyncRecord(async_class, payload)


def parse_stream_record(s: str) -> Optional[StreamRecord]:
    match s[0]:
        case "~":
            stream_type = StreamType.OUTPUT
        case "@":
            stream_type = StreamType.INPUT
        case "&":
            stream_type = StreamType.ERROR
        case _:
            return None
    payload = s[1:].strip('"')
    return StreamRecord(stream_type, payload)


def parse_record(s: str) -> Optional[Record]:
    if s.startswith("^"):
        return parse_result_record(s)
    elif s.startswith("*") or s.startswith("+") or s.startswith("="):
        return parse_async_record(s)
    elif s.startswith("~") or s.startswith("@") or s.startswith("&"):
        return parse_stream_record(s)
    elif s.strip() == "(gdb)":
        return PromptRecord()
    return None
