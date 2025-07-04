# momen

momen is a Python debugger library that wraps GDB/MI to provide an easy-to-use interface for process control and memory access.

## Quick start

```python
import momen

dbg = momen.process("/bin/echo")
dbg.run(args=["Hello", "World"])
```