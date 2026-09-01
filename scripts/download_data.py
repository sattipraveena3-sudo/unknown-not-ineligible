from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

FILES = {
    "qcfy2024_csv.zip": (
        "https://snapqcdata.net/sites/default/files/2026-08/qcfy2024_csv.zip",
        "b8b29b8593f78aa51c48332c47d2d92fa5bbecf5346570acb45e26f2d9ebd2b5",
    ),
    "qcfy2023_csv.zip": (
        "https://snapqcdata.net/sites/default/files/2025-03/qcfy2023_csv.zip",
        "cf79d4d2152b332a4ebd26c49320e3d64fbf65b918b53168d50a52c7bea20648",
    ),
    "FY-2024-Tech-Doc.pdf": (
        "https://snapqcdata.net/sites/default/files/2026-08/FY-2024-Tech-Doc.pdf",
        "d222c7ae7762df5cd4935a9f0dbb303852728282ecac21debe08a94ef8acbb06",
    ),
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://snapqcdata.net/datafiles"},
    )
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)


def main() -> None:
    target = Path("data/raw")
    target.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in FILES.items():
        path = target / name
        if not path.exists() or digest(path) != expected:
            download(url, path)
        actual = digest(path)
        if actual != expected:
            raise RuntimeError(f"Checksum mismatch for {name}: {actual}")
        print(f"verified {name}: {actual}")
    with zipfile.ZipFile(target / "qcfy2024_csv.zip") as archive:
        archive.extract("qc_pub_fy2024.csv", target)
    with zipfile.ZipFile(target / "qcfy2023_csv.zip") as archive:
        archive.extract("qc_pub_fy2023.csv", target)


if __name__ == "__main__":
    main()
