import csv
import os
from urllib.parse import urlparse


_known_domains: set[str] = set()


def load_domains(csv_path: str | None = None) -> None:
    path = csv_path or os.getenv("DOMAINS_CSV_PATH", "./disinfodomains.csv")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row["Domain"].strip().lower()
            if domain:
                _known_domains.add(domain)


def is_known_disinfo_domain(url: str) -> bool:
    host = urlparse(url).hostname or ""
    host = host.lower().removeprefix("www.")
    return host in _known_domains


def extract_domain(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.lower().removeprefix("www.")
