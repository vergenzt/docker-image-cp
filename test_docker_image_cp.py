from contextlib import ExitStack, contextmanager
from pathlib import Path
import subprocess as sp
import sys
import tempfile
import unittest

import docker_image_cp


@contextmanager
def docker_dir(src: str, cnt: str):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, src).write_text(cnt)
        Path(tmp, "Dockerfile").write_text(
            "FROM scratch\n" f"COPY {src} ./\n" "CMD sh\n"
        )
        yield tmp


def run_py(*args: str):
    py_mod = [sys.executable, docker_image_cp.__file__]
    return sp.check_call([*py_mod, *args])


class Tests(unittest.TestCase):
    def test_build_arg(self):
        with ExitStack() as stack:
            src = "foo.txt"
            cnt = "foo bar baz"
            ctx = stack.enter_context(docker_dir(src, cnt))
            dst = stack.enter_context(tempfile.TemporaryDirectory())
            run_py("-b", ctx, src, f"{dst}/{src}")

    def test_no_image(self):
        with self.assertRaises(sp.CalledProcessError):
            run_py("foo", "bar")
