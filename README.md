# phonelint

**Is this number's range actually assigned to anyone?**

`libphonenumber` tells you a number is well-formed and what type it looks like.
It does not tell you whether the range it sits in has been allocated to an
operator — and a number in an unallocated range **cannot ring**, however
perfectly it is formatted.

```python
import phonelint

r = phonelint.lookup("+44 1803 930000")
r.line_type   # 'landline'
r.location    # 'Torquay'
r.allocated   # False  <- this range is published as Free
r.reachable   # False
```

`libphonenumber` calls that same number `FIXED_LINE` and valid. Both are true.
It still cannot ring.

## The comparison, reproducible in ten lines

```python
import phonenumbers, phonelint
from phonenumbers import carrier, number_type

n = phonenumbers.parse("+441803930000", None)
print(number_type(n), repr(carrier.name_for_number(n, "en")))
#  1 ''                       <- FIXED_LINE, no carrier

print(phonelint.lookup("+441803930000"))
#  line_type='landline' location='Torquay' allocated=False reachable=False
```

| | libphonenumber | phonelint |
|---|---|---|
| parse, format, validate | **yes** | delegates to it |
| line type | yes, where ranges allow | from allocation records |
| operator the range was allocated to | often empty | yes, where published |
| **is the range allocated at all** | **no** | **yes** |

This is a companion, not a replacement. Parsing is a solved problem and
`libphonenumber` solved it; this adds the one layer it does not carry.

## Install

```
pip install phonelint
```

`phonenumbers` comes with it. No network calls, no API key, no account. Every
lookup is local.

## Coverage

```python
phonelint.coverage()
# {'+44 GB/GG/IM/JE': 345274}
```

**United Kingdom only, 345,274 prefixes**, from Ofcom's published allocation
records. GB, Guernsey, Jersey and the Isle of Man share one numbering plan and
one dataset.

**The United States is not bundled.** It is where the gap is widest —
`libphonenumber` returns `FIXED_LINE_OR_MOBILE` and an empty carrier for
essentially every US number, because NANP mobile and landline numbers come from
the same ranges and nothing in the digits separates them. The allocation data
that answers it is public, but NANPA publishes no terms of use, only a blanket
copyright footer, and redistributing someone else's data inside a package is a
different act from reading it. The code is country-agnostic; if that is settled
the data drops in without an API change.

## What this does not do

**It does not know about porting.** `carrier` is the operator a *range* was
allocated to. A subscriber who moved network keeps their number, so a ported
number still reports the operator it started with. Resolving that needs a live
query against the routing database, which no offline dataset can answer. If
your use case turns on current network rather than original allocation, this is
not the tool and nothing offline is.

**It does not tell you a number is in service.** An allocated range means
numbers in it *can* exist. Whether a particular one is connected today is a
different question, and again a live one.

**`allocated=False` is the firm half.** That one is deterministic: if the
regulator has assigned the range to nobody, nothing in it rings. Most of the
value in cleaning a list is there.

## API

```python
phonelint.lookup(number: str, region: str | None = None) -> Result
phonelint.enrich(parsed_phonenumber) -> Result
phonelint.coverage() -> dict[str, int]
```

`Result` fields are `None` when unknown and are never guessed:

`number` `country` `valid` `allocated` `line_type` `carrier` `location`
`prefix` `reachable`

`region` is a two-letter code, needed only for numbers written in local format
(`"01803 930000", "GB"`).

## Data licence

Code is MIT. The bundled UK data is separate:

> Contains information licensed under the Open Government Licence v3.0.

See [DATA-LICENCE.md](DATA-LICENCE.md). Ofcom does not endorse this package.

## Related

Built by the people behind [phonelint.com](https://phonelint.com) — a desktop
bulk list cleaner and a free browser tool that does the same allocation check
on a whole file without uploading it.
