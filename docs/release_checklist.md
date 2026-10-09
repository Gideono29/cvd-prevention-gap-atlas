# Release checklist

Zenodo archives each **published GitHub release** and mints a DOI from `.zenodo.json`.

## One-time setup (maintainer)
1. Create the empty GitHub repo `Gideono29/cvd-prevention-gap-atlas` and push `main`.
2. zenodo.org -> Log in with GitHub -> Account menu -> GitHub -> Sync now -> switch the repo **On**.
3. Confirm a `zenodo.org` webhook appears in the repo's Settings -> Webhooks.

## Before v1.0.0
- [ ] Full run on real PLACES, SVI, RUCA, HRSA and WONDER data; outputs reviewed.
- [ ] Weight sensitivity analysis done and documented.
- [ ] Version bumped in `pyproject.toml`, `gapatlas/__init__.py`, `CITATION.cff`; `date-released` set.
- [ ] Source URLs and dataset IDs in `gapatlas/config.py` verified.
- [ ] `pytest -q` passes; Actions green on `main`.

## Release
Draft a release with tag `v1.0.0` from `main`, paste the changelog entry, publish. Then add the concept DOI to
`CITATION.cff` and `README.md`, and replace `[DOI]` on your CV.
