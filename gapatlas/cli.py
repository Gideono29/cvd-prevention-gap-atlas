"""Command line: download | check-release | build."""
import argparse
import sys
from pathlib import Path

import pandas as pd

from .build import assemble, build
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
    sn = sub.add_parser("sensitivity", help="rank stability under alternative weights and measure sets")
    sn.add_argument("--out", default=Path("outputs"), type=Path)
    st = sub.add_parser("site", help="generate static map site data (needs the `site` extra)")
    st.add_argument("--site-dir", default=Path("site"), type=Path)
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
    elif a.cmd == "sensitivity":
        from .sensitivity import run
        frames, _, _ = assemble(a.data_dir)
        res = pd.concat([run(df, lvl) for lvl, df in frames.items()], ignore_index=True)
        a.out.mkdir(parents=True, exist_ok=True)
        res.to_csv(a.out / "sensitivity_summary.csv", index=False)
        print(res.to_string(index=False))
    elif a.cmd == "site":
        from .sitegen import generate
        print(generate(a.data_dir, a.site_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
