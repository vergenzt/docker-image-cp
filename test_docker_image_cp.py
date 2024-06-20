from contextlib import ExitStack, contextmanager
from pathlib import Path
import subprocess as sp
import sys
import tempfile
from typing import List
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


def docker_ids(cmd: List[str]):
    return set(sp.check_output(cmd, text=True).splitlines())


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

    def test_image_arg(self):
        with ExitStack() as stack:
            src = "preexisting.txt"
            cnt = "hello, world!"
            ctx = stack.enter_context(docker_dir(src, cnt))
            img = sp.check_output(["docker", "build", "-q", ctx], text=True).strip()
            dst = stack.enter_context(tempfile.TemporaryDirectory())
            run_py("-i", img, src, f"{dst}/{src}")

    def test_no_cleanup_arg_imgs(self):
        imgs_cmd = ["docker", "images", "-q"]
        imgs_before = docker_ids(imgs_cmd)
        self.test_build_arg()
        imgs_after = docker_ids(imgs_cmd)
        self.assertSetEqual(imgs_before, imgs_after)

    def test_no_cleanup_arg_cnts(self):
        cnts_cmd = ["docker", "ps", "-q"]
        cnts_before = docker_ids(cnts_cmd)
        self.test_build_arg()
        cnts_after = docker_ids(cnts_cmd)
        self.assertSetEqual(cnts_before, cnts_after)

    def test_no_image_arg(self):
        with self.assertRaises(sp.CalledProcessError):
            run_py("foo", "bar")
