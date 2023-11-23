import os
import signal
from dataclasses import dataclass
from typing import IO, Any, Callable
from threading import Condition
from threading import Thread
from multiprocessing import Queue
import subprocess

@dataclass
class ShellResult:
    killed: bool
    exit_code: int|None

def Shell(cmd: str, on_out: Callable[[str], Any]|None=None, on_err: Callable[[str], Any]|None=None):
    killed = False
    with LiveShell() as shell:
        if on_out is not None: shell.RegisterOnOut(lambda x: on_out(shell.Decode(x)))
        if on_err is not None: shell.RegisterOnErr(lambda x: on_err(shell.Decode(x)))
        try:
            shell.Write(cmd)
            shell.Write(f"exit")
            shell._console.wait()
        except KeyboardInterrupt:
            killed = True
            try:
                os.killpg(os.getpgid(shell.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
    return ShellResult(killed, shell._console.poll())

class LiveShell:
    class Pipe:
        def __init__(self, io:IO[bytes]|None, lock: Condition=Condition(), q: Queue=Queue()) -> None:
            assert io is not None
            self.IO = io
            self.Lock = lock
            self.Q = q

        def __enter__(self):
            self.Lock.acquire()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.Lock.release()

    def __init__(self) -> None:
        console = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._console = console
        self._in = LiveShell.Pipe(console.stdin)
        self._out = LiveShell.Pipe(console.stdout)
        self._err = LiveShell.Pipe(console.stderr)
        self._onCloseLock = Condition()
        self._closed = False
        self.pid = console.pid
        self._on_out_callbacks = []
        self._on_err_callbacks = []

        workers: list[Thread] = []
        def reader(pipe: LiveShell.Pipe, callbacks):
            io = iter(pipe.IO.readline, b'')
            while True:
                if self.IsClosed():
                    return
                try:
                    line = next(io, None)
                    if line is None: continue
                except ValueError:
                    break
                for cb in callbacks: cb(line)
                with pipe:
                    pipe.Q.put(line)
        workers.append(Thread(target=reader, args=[self._out, self._on_out_callbacks]))
        workers.append(Thread(target=reader, args=[self._err, self._on_err_callbacks]))

        for w in workers:
            w.daemon = True # stop with program
            w.start()

    def Send(self, payload: bytes):
        stdin = self._in
        with self._in:
            stdin.IO.write(payload)
            stdin.IO.flush()
    
    def Decode(self, payload: bytes):
        return payload.decode()

    def Write(self, msg: str):
        self.Send(bytes('%s\n' % (msg), encoding="utf-8"))

    def RegisterOnOut(self, callback: Callable[[bytes], None]):
        self._on_out_callbacks.append(callback)

    def RegisterOnErr(self, callback: Callable[[bytes], None]):
        self._on_err_callbacks.append(callback)

    def RemoveOnOut(self, callback: Callable[[bytes], None]):
        self._on_out_callbacks.remove(callback)

    def RemoveOnErr(self, callback: Callable[[bytes], None]):
        self._on_err_callbacks.remove(callback)

    def PollRead(self):
        def _r(p: LiveShell.Pipe):
            with p:
                q = p.Q
                while not q.empty():
                    yield q.get_nowait()

        errs = list(_r(self._err))
        outs = list(_r(self._out))
        return errs, outs
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Dispose()
        return

    def IsClosed(self):
        with self._onCloseLock:
            return self._closed

    def Dispose(self):
        with self._onCloseLock:
            if self._closed:
                return
            self._closed = True
            self._onCloseLock.notify_all()

        self._console.terminate()
