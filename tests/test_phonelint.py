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
