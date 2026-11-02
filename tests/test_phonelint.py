"""Tests pinned to real published ranges, not to invented numbers.

Every expectation below is checked against the bundled Ofcom extract rather
than asserted from memory, because a test that encodes a guess passes forever
and proves nothing.
"""
import phonenumbers
import pytest

import phonelint


def test_coverage_reports_one_dataset_not_four():
    cov = phonelint.coverage()
    assert len(cov) == 1, "GB/GG/JE/IM share one plan and must not be counted four times"
    assert next(iter(cov.values())) > 300_000


def test_allocated_mobile_returns_its_operator():
    r = phonelint.lookup("+447911123456")
    assert r.line_type == "mobile"
    assert r.carrier                      # an operator, whichever it is
    assert r.allocated is True
    assert r.reachable is True


def test_free_range_is_reported_unreachable():
    # 01803 930xxx is published as Free: correctly formatted, cannot ring.
    r = phonelint.lookup("+441803930000")
    assert r.valid is True, "libphonenumber considers it a possible number"
    assert r.allocated is False
    assert r.reachable is False, "this is the distinction the package exists for"


def test_channel_islands_resolve_to_the_uk_plan():
    # libphonenumber returns GG for this, not GB. Mapping only GB silently
    # missed every Guernsey, Jersey and Isle of Man number.
    r = phonelint.lookup("+447911123456")
    assert r.country in {"GG", "GB", "JE", "IM"}
    assert r.line_type is not None


def test_longest_prefix_wins():
    r = phonelint.lookup("+442079460958")
    assert r.prefix and len(r.prefix) >= 5
    assert r.location


def test_unknown_country_degrades_without_guessing():
    r = phonelint.lookup("+12125550147")        # US: no data bundled
    assert r.country == "US"
    assert r.line_type is None and r.carrier is None
    assert r.allocated is None, "absent data must read as unknown, never as False"
    assert r.reachable is None


def test_garbage_input_does_not_raise():
    for bad in ["", "not a number", "+", "++44", "0000"]:
        assert phonelint.lookup(bad).line_type is None


def test_local_format_needs_a_region():
    assert phonelint.lookup("01803 930000").country is None
    assert phonelint.lookup("01803 930000", "GB").country == "GB"


def test_enrich_accepts_a_parsed_number():
    n = phonenumbers.parse("+441803930000", None)
    assert phonelint.enrich(n).allocated is False


def test_it_adds_what_libphonenumber_does_not():
    """The package's entire reason for existing, as an assertion."""
    from phonenumbers import carrier, number_type, PhoneNumberType
    n = phonenumbers.parse("+441803930000", None)
    assert carrier.name_for_number(n, "en") == ""      # libphonenumber: nothing
    assert phonelint.lookup("+441803930000").location  # ours: Torquay


# Ofcom publishes these ranges for TV and radio drama and does not issue them.
# They are public, reproducible, and they are what 0.1.0 got wrong: all four
# came back allocated and reachable, which is the exact opposite of the truth
# and contradicts the one claim this dataset exists to support.
# https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/numbers-for-drama
DRAMA = [
    "+442079460000", "+442079460999",   # London   020 7946 0xxx
    "+441134960000", "+441134960999",   # Leeds    0113 496 0xxx
    "+441184960000",                    # Reading  0118 496 0xxx
    "+447700900000", "+447700900999",   # mobile   07700 900xxx
]


def test_drama_ranges_are_not_allocated():
    for n in DRAMA:
        r = phonelint.lookup(n)
        assert r.allocated is False, f"{n} reported allocated={r.allocated}"
        assert r.reachable is False, f"{n} reported reachable={r.reachable}"


def test_real_numbers_keep_their_operator():
    # The counterweight: the fix must not make everything unallocated.
    for n in ("+442072193000", "+442079304832", "+443700100222"):
        r = phonelint.lookup(n)
        assert r.allocated is True, f"{n} reported allocated={r.allocated}"
        assert r.carrier, f"{n} allocated with no operator named"


def test_invalid_numbers_still_reach_the_allocation_data():
    # libphonenumber returns no region for numbers it calls invalid, which used
    # to skip the lookup entirely. The mobile drama range is one of those.
    r = phonelint.lookup("+447700900000")
    assert r.country == "GB"
    assert r.allocated is False
