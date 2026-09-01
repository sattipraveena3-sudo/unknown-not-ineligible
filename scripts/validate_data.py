from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

EXPECTED = {
    2024: {
        "file": "qc_pub_fy2024.csv", "rows": 44_891, "columns": 1_177,
        "csv_sha256": "e871a8e9caca0be72e2003b09bdf71e1d020984b52289d2b74c4c6b88c4f793b",
        "status_counts": {1: 27_055, 2: 10_734, 3: 7_102},
    },
    2023: {
        "file": "qc_pub_fy2023.csv", "rows": 43_776, "columns": 854,
        "csv_sha256": "e7e88d59c6ebf145f968a45b72a6fc368d213d8ed0b3c96e34cb7797abc5a045",
        "status_counts": {1: 26_832, 2: 10_131, 3: 6_813},
    },
}


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    required = {"CAT_ELIG", "FSELDER", "FSDIS", "FSGRINC", "GROSSCRN", "FSNETINC",
                "NETSCRN", "FSASSET", "ASSLIM", "FSGRTEST", "FSNETEST", "FSASTEST"}
    for year, expected in EXPECTED.items():
        path = Path("data/raw") / expected["file"]
        if not path.exists():
            raise SystemExit("Run `make download` first.")
        if sha256(path) != expected["csv_sha256"]:
            raise RuntimeError(f"CSV checksum mismatch for FY{year}")
        frame = pd.read_csv(path)
        assert frame.shape == (expected["rows"], expected["columns"]), frame.shape
        counts = frame["STATUS"].value_counts().sort_index().to_dict()
        assert counts == expected["status_counts"], counts
        assert required <= set(frame.columns)
        print(f"PASS FY{year}: {len(frame):,} rows, {len(frame.columns):,} columns")


if __name__ == "__main__":
    main()
