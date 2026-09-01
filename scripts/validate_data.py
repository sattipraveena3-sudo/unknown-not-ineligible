from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

EXPECTED = {
    "rows": 44_891,
    "columns": 1_177,
    "csv_sha256": "e871a8e9caca0be72e2003b09bdf71e1d020984b52289d2b74c4c6b88c4f793b",
    "status_counts": {1: 27_055, 2: 10_734, 3: 7_102},
}


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    path = Path("data/raw/qc_pub_fy2024.csv")
    if not path.exists():
        raise SystemExit("Run `make download` first.")
    if sha256(path) != EXPECTED["csv_sha256"]:
        raise RuntimeError("CSV checksum does not match the audited August 2026 release")
    frame = pd.read_csv(path)
    assert frame.shape == (EXPECTED["rows"], EXPECTED["columns"]), frame.shape
    counts = frame["STATUS"].value_counts().sort_index().to_dict()
    assert counts == EXPECTED["status_counts"], counts
    required = {
        "CAT_ELIG", "FSELDER", "FSDIS", "FSGRINC", "GROSSCRN", "FSNETINC",
        "NETSCRN", "FSASSET", "ASSLIM", "FSGRTEST", "FSNETEST", "FSASTEST",
    }
    assert required <= set(frame.columns)
    print(f"PASS: {len(frame):,} rows, {len(frame.columns):,} columns, official status totals reproduced")


if __name__ == "__main__":
    main()

