from momen.gdbmi.parser import (
    split_fields,
    parse_async_record,
    parse_key_value,
    parse_list,
    parse_record,
    parse_result_record,
    parse_stream_record,
    parse_tuple,
    parse_value,
)
from momen.gdbmi.record import StreamType, PromptRecord


def test_split_fields():
    assert split_fields("") == []
    assert split_fields("a,b,c") == ["a", "b", "c"]
    assert split_fields("a,{b,c},d") == ["a", "{b,c}", "d"]
    assert split_fields('a,{b,{c="d"}},[e,f],"g,h"') == [
        "a",
        '{b,{c="d"}}',
        "[e,f]",
        '"g,h"',
    ]


def test_parse_list():
    assert parse_list("") == []
    assert parse_list('"a","b","c"') == ["a", "b", "c"]
    assert parse_list('{a="1"},{b="2",c="3"}') == [{"a": "1"}, {"b": "2", "c": "3"}]
    assert parse_list('"a",{b="1",c="2"},["d","e"]') == [
        "a",
        {"b": "1", "c": "2"},
        ["d", "e"],
    ]
    assert parse_list('a="1",b={c="2",d="3"},e="4"') == [
        {"a": "1"},
        {"b": {"c": "2", "d": "3"}},
        {"e": "4"},
    ]


def test_parse_value():
    assert parse_value('"test"') == "test"
    assert parse_value('{a="1"}') == {"a": "1"}
    assert parse_value('["1","2","3"]') == ["1", "2", "3"]


def test_parse_tuple():
    assert parse_tuple("") == {}
    assert parse_tuple('a="1",b="2"') == {"a": "1", "b": "2"}
    assert parse_tuple('a="1",b={c="2",d="3"}') == {"a": "1", "b": {"c": "2", "d": "3"}}


def test_parse_key_value():
    assert parse_key_value('a="1"') == ("a", "1")
    assert parse_key_value('b={c="2",d="3"}') == ("b", {"c": "2", "d": "3"})
    assert parse_key_value('e=["4","5"]') == ("e", ["4", "5"])


def test_parse_result_record():
    raw_record = '^done,name="test",value="42"'
    record = parse_result_record(raw_record)
    assert record is not None
    assert record.result_class == "done"
    assert record.payload == {"name": "test", "value": "42"}


def test_parse_async_record():
    raw_record = '*stopped,reason="breakpoint-hit",frame={addr="0x401000",func="main",args=[],arch="i386:x86-64"},thread-id="1"'
    record = parse_async_record(raw_record)
    assert record is not None
    assert record.async_class == "stopped"
    assert record.payload == {
        "reason": "breakpoint-hit",
        "frame": {
            "addr": "0x401000",
            "func": "main",
            "args": [],
            "arch": "i386:x86-64",
        },
        "thread-id": "1",
    }


def test_parse_stream_record():
    raw_record = '@"input"'
    record = parse_stream_record(raw_record)
    assert record is not None
    assert record.stream_type == StreamType.INPUT
    assert record.payload == "input"

    raw_record = '~"Hello, world!"'
    record = parse_stream_record(raw_record)
    assert record is not None
    assert record.stream_type == StreamType.OUTPUT
    assert record.payload == "Hello, world!"

    raw_record = '&"Error message"'
    record = parse_stream_record(raw_record)
    assert record is not None
    assert record.stream_type == StreamType.ERROR
    assert record.payload == "Error message"


def test_parse_prompt_record():
    assert isinstance(parse_record("(gdb)"), PromptRecord)
