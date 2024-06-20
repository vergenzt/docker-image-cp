"""
Copy files out of a Docker image.
"""

import argparse
import json
import shlex
import subprocess as sp
import sys
import tempfile
from collections import defaultdict
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Iterator, List, Optional, Tuple


@contextmanager
def tmp_image(buildctx: Path) -> Iterator[str]:
    with tempfile.TemporaryDirectory() as tmp:
        iidf = Path(tmp, "iid")
        sp.check_call(["docker", "build", f"--iidfile={iidf}", buildctx])
        iid = iidf.read_text()
        try:
            yield iid
        finally:
            # attempt to remove the image, but swallow failure
            sp.run(["docker", "rmi", iid])


@contextmanager
def tmp_container(iid: str) -> Iterator[str]:
    cid = sp.check_output(["docker", "create", iid], text=True).strip()
    try:
        yield cid
    finally:
        sp.check_call(["docker", "rm", cid])


def img_workdir(iid: str) -> Path:
    info = json.loads(sp.check_output(["docker", "inspect", iid]))
    return Path(info[0]["Config"]["WorkingDir"])


@dataclass
class Args:
    SRC: Path = field(
        metadata=dict(
            help="Source path to copy from within the image. May be relative, in which case it's relative to the image's workdir."
        )
    )
    DST: Path = field(
        metadata=dict(
            nargs="?",
            help="Dest path on host to copy to. Defaults to SRC if SRC is relative, else DST is required.",
        )
    )
    image: str = field(
        metadata=dict(
            opts=("-i", "--image"),
            exgroup="image",
            metavar="IID",
            help="ID of a pre-existing image to copy from",
        )
    )
    build: Path = field(
        metadata=dict(
            opts=("-b", "--build"),
            exgroup="image",
            metavar="CTX",
            help="Context path for building an image to copy from",
        )
    )

    def __post_init__(self):
        assert self.SRC
        assert (
            self.DST or not self.SRC.is_absolute()
        ), "Must specify DST if SRC is absolute"

    @classmethod
    def from_args(cls, argv: Optional[List[str]] = None):
        parser = argparse.ArgumentParser()
        grps = defaultdict(
            lambda: parser.add_mutually_exclusive_group(required=True),
            dict[str, Any](),  # for type inference
        )
        for fld in fields(cls):
            meta = dict(fld.metadata)
            (grps[meta.pop("exgroup")] if "exgroup" in meta else parser).add_argument(
                *(meta.pop("opts") if "opts" in meta else [fld.name]),
                type=fld.type,
                **meta,
            )
        try:
            return cls(**parser.parse_args(argv).__dict__)  # type: ignore
        except (AssertionError, ValueError) as err:
            parser.error(*err.args)


def log_subprocess(event: str, evt_args: Tuple[Any, ...]):
    if event == "subprocess.Popen":
        _executable, args, _cwd, _env = evt_args
        print("+ " + shlex.join(map(str, args)), file=sys.stderr)


def main(argv: Optional[List[str]] = None):
    sys.addaudithook(log_subprocess)
    with ExitStack() as stack:
        with_ = stack.enter_context
        try:
            args = Args.from_args(argv=argv)

            if not (iid := args.image):
                assert args.build
                iid = with_(tmp_image(args.build))

            assert args.SRC
            src_path = (
                args.SRC if args.SRC.is_absolute() else img_workdir(iid) / args.SRC
            )
            dst_path = args.DST or args.SRC

            cid = with_(tmp_container(iid))
            sp.check_call(["docker", "cp", f"{cid}:{src_path}", dst_path])

        except sp.CalledProcessError as e:
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            stack.close()
            sys.exit(130)


if __name__ == "__main__":
    main()