#!/usr/bin/env python3
"""Generate a non-Russian IP/DNS/WebRTC checker geosite category.

Input: v2fly/domain-list-community checkout in community/data.
Output: community/data/ip-check-foreign and optional plain-text report.

Russian ownership on non-Russian TLDs cannot be inferred reliably: add such
sites to the curated exclusions file. Fails closed if upstream adds patterns
that cannot be filtered correctly.
"""

import argparse
from pathlib import Path

RUSSIAN_TLDS = ("ru", "su", "xn--p1ai", "xn--p1acf")  # .ru, .su, .рф, .рус


def domain_ascii(host: str) -> str:
    return host.rstrip(".").lower().encode("idna").decode("ascii")


def parse_exclusions(path: Path) -> set[str]:
    result = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            result.add(domain_ascii(line))
    return result


def resolve(name: str, data_dir: Path, stack: tuple[str, ...] = ()):
    """Expand nested includes, respecting v2fly include attribute filters."""
    if name in stack:
        raise ValueError(f"Cyclic include: {' -> '.join(stack + (name,))}")
    path = data_dir / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing geosite source: {path}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        first, *attrs = tokens
        if first.startswith("include:"):
            included = first.removeprefix("include:")
            must = {a[1:] for a in attrs if a.startswith("@") and not a.startswith("@-")}
            ban = {a[2:] for a in attrs if a.startswith("@-")}
            for item, item_attrs in resolve(included, data_dir, stack + (name,)):
                actual = {a[1:] for a in item_attrs}
                if must.issubset(actual) and not ban.intersection(actual):
                    yield item, item_attrs
        else:
            # Attribute annotations (e.g. @cn) remain in the derived category.
            # Affiliation markers (&...) are intentionally not copied.
            yield first, tuple(a for a in attrs if a.startswith("@"))


def foreign(entry: str, excluded: set[str]) -> bool:
    if entry.startswith(("keyword:", "regexp:")):
        raise ValueError(f"Cannot safely country-filter a matching pattern: {entry}")
    if entry.startswith(("domain:", "full:")):
        _, host = entry.split(":", 1)
    elif ":" not in entry:
        host = entry
    else:
        raise ValueError(f"Unexpected source entry: {entry}")
    host = domain_ascii(host)
    tld = host.rsplit(".", 1)[-1]
    if tld in RUSSIAN_TLDS:
        return False
    # Exact hostname and subdomains, but not lookalikes (example.ru.com).
    return not any(host == e or host.endswith("." + e) for e in excluded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--exclude-file", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    excluded = parse_exclusions(args.exclude_file)
    selected: set[str] = set()
    rejected: set[str] = set()
    for entry, attrs in resolve("category-ip-geo-detect", args.data_dir):
        # Normalize optional "domain:" syntax to one form.
        key = entry + (" " + " ".join(attrs) if attrs else "")
        if foreign(entry, excluded):
            selected.add(key)
        else:
            rejected.add(key)

    if not selected or len(selected) < 100:
        raise ValueError(f"Unexpectedly small category ({len(selected)} domains)")

    destination = args.data_dir / "ip-check-foreign"
    destination.write_text(
        "# Auto-generated from v2fly/category-ip-geo-detect. Do not edit manually.\n"
        + "# Russian domains filtered by TLD and ip-check-ru-exclude.txt.\n"
        + "\n".join(sorted(selected)) + "\n", encoding="utf-8"
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(sorted(selected)) + "\n", encoding="utf-8")
    print(f"ip-check-foreign: {len(selected)} rules, excluded: {len(rejected)}")
    print(f"Wrote: {destination}")


if __name__ == "__main__":
    main()
