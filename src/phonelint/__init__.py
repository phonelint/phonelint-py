"""Carrier and line type for phone numbers, from published numbering plans.

libphonenumber parses and formats; it does not tell you who a number belongs to.
For a UK or US number its `carrier` is usually empty and its type is often
FIXED_LINE_OR_MOBILE, because that is as far as range metadata goes. This fills
exactly that gap and nothing else:

    >>> import phonelint
    >>> r = phonelint.lookup("+44 1803 930000")
    >>> r.line_type, r.location, r.allocated
    ('landline', 'Torquay', False)

It is built ON libphonenumber rather than against it. Parsing, validation and
formatting are delegated to `phonenumbers`, which does them well. What is added
is the block the number sits in, taken from the regulator's own allocation
records.

The most useful field is the one nobody else returns: `allocated`. A number in
a range no operator has been assigned **cannot ring**, whatever its shape. That
is deterministic, and it is where most of the value in list cleaning sits.

Coverage: United Kingdom, 345,274 prefixes. United States is not bundled — see
the README; the data exists but its redistribution terms do not permit shipping
it here yet.
"""
from __future__ import annotations

import functools
import pathlib
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:                       # pragma: no cover
    import phonenumbers

__all__ = ["lookup", "Result", "enrich", "coverage", "__version__"]

# Read from the installed metadata rather than restating it here. Hand-written
# version strings drift: 0.1.1 shipped to PyPI with pyproject saying 0.1.1 and
# this line still saying 0.1.0, so phonelint.__version__ reported the wrong
# release to anyone who asked. pyproject.toml is the one source of truth.
try:
    from importlib.metadata import PackageNotFoundError, version as _dist_version
    try:
        __version__ = _dist_version("phonelint")
    except PackageNotFoundError:          # running from a source tree, not installed
        __version__ = "0.0.0+source"
except ImportError:                       # pragma: no cover - importlib.metadata is 3.8+
    __version__ = "0.0.0+unknown"

_DATA = pathlib.Path(__file__).parent / "_data"
# +44 is one numbering plan across four jurisdictions. libphonenumber returns
# the ISO region, so a Guernsey or Jersey number comes back GG or JE and would
# miss the dataset entirely — a mobile that resolved to "Guernsey" was the bug
# that found this.
_SUPPORTED = {"GB": "uk.db", "GG": "uk.db", "JE": "uk.db", "IM": "uk.db"}


@dataclass(frozen=True)
class Result:
    """What is known about a number. Fields are None when unknown, never guessed."""

    number: str
    country: Optional[str] = None
    valid: Optional[bool] = None          # from libphonenumber: is it a possible number
    allocated: Optional[bool] = None      # is its block assigned to an operator
    line_type: Optional[str] = None       # landline | mobile | voip | freephone | ...
    carrier: Optional[str] = None         # the operator the BLOCK was allocated to
    location: Optional[str] = None        # the exchange area, where published
    prefix: Optional[str] = None          # the block that matched

    @property
    def reachable(self) -> Optional[bool]:
        """False when the number provably cannot ring. None when not known.

        A number outside an allocated block is dead regardless of how well it
        is formatted, and that is the one judgement here that is deterministic
        rather than probabilistic.
        """
        if self.valid is False or self.allocated is False:
            return False
        if self.valid and self.allocated:
            return True
        return None


@functools.lru_cache(maxsize=4)
def _db(country: str) -> Optional[sqlite3.Connection]:
    name = _SUPPORTED.get(country)
    if not name:
        return None
    path = _DATA / name
    if not path.exists():
        return None
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)


def coverage() -> dict[str, int]:
    """Prefix count per bundled DATASET, so callers can check before relying on it.

    Keyed by dataset, not by region: GB, GG, JE and IM share one numbering plan
    and one file, and reporting 345,274 four times would imply four times the
    data.
    """
    out = {}
    for name in sorted(set(_SUPPORTED.values())):
        path = _DATA / name
        if not path.exists():
            continue
        regions = sorted(k for k, v in _SUPPORTED.items() if v == name)
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        out["+44 " + "/".join(regions)] = db.execute(
            "SELECT COUNT(*) FROM blocks").fetchone()[0]
        db.close()
    return out


def _match(db: sqlite3.Connection, national: str):
    """Longest matching block.

    Allocation records are published at several depths — a six-digit range and
    a seven-digit range can both exist, and the longer one is the more specific
    truth. Matching shortest-first would answer with the parent block and get
    the operator wrong whenever a range has been subdivided.
    """
    for end in range(len(national), 2, -1):
        row = db.execute(
            "SELECT prefix, line_type, carrier, location, allocated "
            "FROM blocks WHERE prefix = ?", (national[:end],)
        ).fetchone()
        if row:
            return row
    return None


def lookup(number: str, region: Optional[str] = None) -> Result:
    """Look up `number`. `region` is a two-letter code for local-format input."""
    import phonenumbers

    try:
        parsed = phonenumbers.parse(number, region)
    except phonenumbers.NumberParseException:
        return Result(number=number)

    country = phonenumbers.region_code_for_number(parsed)
    if country is None:
        # libphonenumber returns no region for numbers it considers invalid,
        # which skipped the allocation check entirely -- exactly the numbers most
        # worth checking. Ofcom's drama mobile range 07700 900xxx came back all
        # None instead of "not allocated". Fall back to the region that owns the
        # country code, so the data still gets consulted.
        country = phonenumbers.region_code_for_country_code(parsed.country_code)
        if country == "ZZ":
            country = None
    valid = phonenumbers.is_valid_number(parsed)
    national = str(parsed.national_number)

    db = _db(country or "")
    if db is None:
        # No data bundled for this country. Report what libphonenumber knows
        # and leave the rest None rather than inventing a confident blank.
        return Result(number=number, country=country, valid=valid)

    row = _match(db, national)
    if row is None:
        return Result(number=number, country=country, valid=valid, allocated=False)

    prefix, line_type, carrier, location, allocated = row
    return Result(number=number, country=country, valid=valid,
                  allocated=bool(allocated), line_type=line_type,
                  carrier=carrier or None, location=location or None,
                  prefix=prefix)


def enrich(parsed: "phonenumbers.PhoneNumber") -> Result:
    """Same as `lookup`, for a number already parsed by `phonenumbers`."""
    import phonenumbers
    return lookup(phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.E164))
