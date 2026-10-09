"""Command line: download | check-release | build."""
import argparse
import sys
from pathlib import Path

from .build import build
from .config import IndexSpec
from .download import check_release, download_places


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="gapatlas", description="CVD Prevention Gap Atlas")
    p.add_argument("--data-dir", default="data", type=Path)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download", help="download PLACES county and tract files")
    sub.add_parser("check-release", help="exit 10 if CDC has published a newer PLACES release")
    b = sub.add_parser("build", help="join sources and compute gap tables")
    b.add_argument("--out", default=Path("outputs"), type=Path)
    b.add_argument("--w-mortality", type=float, default=1.0, help="weight of WONDER mortality in burden")
    b.add_argument("--w-hpsa", type=float, default=1.0, help="weight of HPSA in capacity")
    a = p.parse_args(argv)

    if a.cmd == "download":
        download_places(a.data_dir)
    elif a.cmd == "check-release":
        res = check_release(a.data_dir)
        print(res)
        return 10 if res["new_release"] else 0
    elif a.cmd == "build":
        spec = IndexSpec(burden_weight_mortality=a.w_mortality, capacity_weight_hpsa=a.w_hpsa)
        print(build(a.data_dir, a.out, spec)["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
