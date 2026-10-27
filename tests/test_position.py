"""Tests for uss_cyclops.position. Every fixture is invented and labelled SYNTHETIC: the coordinates are fictional
open-ocean waypoints, not ship fixes, and nothing here is research evidence."""

import json
import math
import unittest
from dataclasses import replace

from uss_cyclops.position import (
    DOCUMENTED,
    HYPOTHESIZED,
    KINDS,
    LAST_CONFIRMED,
    PositionRecord,
    PositionRecordError,
    check_record,
    export_json,
    export_record,
    reclassify,
    validate_record,
)


def documented(**overrides):
    values = dict(
        record_id="SYNTHETIC-DOC-1",
        kind=DOCUMENTED,
        latitude=-35.123456,
        longitude=-120.654321,
        uncertainty_nm=5.0,
        source_id="SYNTHETIC-SOURCE-A",
        page="12",
        evidence=("SYNTHETIC: invented log entry",),
    )
    values.update(overrides)
    return PositionRecord(**values)


def hypothesized(**overrides):
    values = dict(
        record_id="SYNTHETIC-HYP-1",
        kind=HYPOTHESIZED,
        latitude=-40.567891,
        longitude=80.254321,
        uncertainty_nm=60.0,
        evidence=("SYNTHETIC: invented drift estimate",),
        counterevidence=("SYNTHETIC: invented sighting elsewhere",),
    )
    values.update(overrides)
    return PositionRecord(**values)


def mentions(errors, word):
    return any(word in error for error in errors)


class ValidationTests(unittest.TestCase):
    def test_valid_documented_record_passes(self):
        self.assertEqual(validate_record(documented()), [])

    def test_valid_last_confirmed_record_passes(self):
        record = documented(kind=LAST_CONFIRMED, page=3)
        self.assertEqual(validate_record(record), [])

    def test_valid_hypothesized_record_passes_without_source(self):
        self.assertEqual(validate_record(hypothesized()), [])

    def test_coordinate_boundaries_are_accepted(self):
        self.assertEqual(validate_record(hypothesized(latitude=90, longitude=-180)), [])
        self.assertEqual(validate_record(hypothesized(latitude=-90, longitude=180)), [])

    def test_latitude_out_of_range_is_rejected(self):
        for latitude in (90.0001, -91, 400):
            self.assertTrue(mentions(validate_record(documented(latitude=latitude)), "latitude"), latitude)

    def test_longitude_out_of_range_is_rejected(self):
        for longitude in (180.5, -180.0001, 720):
            self.assertTrue(mentions(validate_record(documented(longitude=longitude)), "longitude"), longitude)

    def test_non_numeric_coordinates_are_rejected(self):
        for bad in (True, float("nan"), float("inf"), "10.5", None):
            self.assertTrue(mentions(validate_record(hypothesized(latitude=bad)), "latitude"), bad)
            self.assertTrue(mentions(validate_record(hypothesized(longitude=bad)), "longitude"), bad)

    def test_unknown_kind_is_rejected(self):
        for kind in ("fact", "Documented", "", None):
            self.assertTrue(mentions(validate_record(documented(kind=kind)), "kind"), kind)
        self.assertEqual(KINDS, ("documented", "last_confirmed", "hypothesized"))

    def test_sourced_kinds_need_source_id_and_page(self):
        for kind in (DOCUMENTED, LAST_CONFIRMED):
            no_source = validate_record(documented(kind=kind, source_id=None))
            self.assertTrue(mentions(no_source, "source_id"), kind)
            blank_source = validate_record(documented(kind=kind, source_id="  "))
            self.assertTrue(mentions(blank_source, "source_id"), kind)
            for page in (None, "", 0, True):
                self.assertTrue(mentions(validate_record(documented(kind=kind, page=page)), "page"), (kind, page))

    def test_uncertainty_is_required_for_every_kind(self):
        for record in (documented(), documented(kind=LAST_CONFIRMED), hypothesized()):
            errors = validate_record(replace(record, uncertainty_nm=None))
            self.assertTrue(mentions(errors, "uncertainty_nm"), record.kind)

    def test_uncertainty_must_be_non_negative_number(self):
        for bad in (-0.1, float("nan"), "5", False):
            self.assertTrue(mentions(validate_record(documented(uncertainty_nm=bad)), "uncertainty_nm"), bad)
        self.assertEqual(validate_record(documented(uncertainty_nm=0)), [])

    def test_hypothesized_needs_counterevidence_or_limits_note(self):
        bare = hypothesized(counterevidence=(), limits_note="")
        self.assertTrue(mentions(validate_record(bare), "counterevidence or a limits_note"))
        blank_note = hypothesized(counterevidence=(), limits_note="   ")
        self.assertTrue(mentions(validate_record(blank_note), "counterevidence or a limits_note"))
        with_note = hypothesized(counterevidence=(), limits_note="SYNTHETIC: invented limit, no source states this")
        self.assertEqual(validate_record(with_note), [])

    def test_evidence_lists_must_hold_non_empty_strings(self):
        self.assertTrue(mentions(validate_record(documented(evidence=("",))), "evidence"))
        self.assertTrue(mentions(validate_record(documented(evidence="SYNTHETIC: a string")), "evidence"))
        self.assertTrue(mentions(validate_record(hypothesized(counterevidence=(3,))), "counterevidence"))
        self.assertEqual(validate_record(documented(evidence=[], counterevidence=[])), [])

    def test_time_is_optional_but_needs_a_precision(self):
        self.assertEqual(validate_record(documented(time="1900-01-02", time_precision="day")), [])
        self.assertTrue(mentions(validate_record(documented(time="1900-01-02")), "time_precision"))
        self.assertTrue(mentions(validate_record(documented(time="1900-01", time_precision="week")), "time_precision"))
        self.assertTrue(mentions(validate_record(documented(time_precision="day")), "time_precision"))

    def test_check_record_raises_with_every_error(self):
        bad = hypothesized(latitude=95, longitude=200, uncertainty_nm=None)
        with self.assertRaises(PositionRecordError) as caught:
            check_record(bad)
        self.assertEqual(len(caught.exception.errors), 3)
        self.assertIs(check_record(documented()), documented() if False else check_record(documented()))


class ReclassifyTests(unittest.TestCase):
    def test_hypothesis_can_never_become_documented_or_last_confirmed(self):
        for kind in (DOCUMENTED, LAST_CONFIRMED):
            with self.assertRaises(PositionRecordError):
                reclassify(hypothesized(source_id="SYNTHETIC-SOURCE-A", page="1"), kind)

    def test_hypothesis_relabelled_by_hand_without_source_fails(self):
        relabelled = replace(hypothesized(), kind=DOCUMENTED)
        errors = validate_record(relabelled)
        self.assertTrue(mentions(errors, "source_id"))
        self.assertTrue(mentions(errors, "page"))

    def test_documented_can_be_downgraded_only_with_limits(self):
        with self.assertRaises(PositionRecordError):
            reclassify(documented(), HYPOTHESIZED)
        downgraded = reclassify(documented(limits_note="SYNTHETIC: invented limit"), HYPOTHESIZED)
        self.assertEqual(downgraded.kind, HYPOTHESIZED)


class ExportTests(unittest.TestCase):
    def test_share_exact_defaults_to_false(self):
        self.assertIs(hypothesized().share_exact, False)
        self.assertIs(documented().share_exact, False)
        self.assertIs(export_record(hypothesized())["share_exact"], False)

    def test_hypothesized_coordinates_are_rounded(self):
        out = export_record(hypothesized(), decimals=2)
        self.assertEqual((out["latitude"], out["longitude"]), (-40.57, 80.25))
        self.assertTrue(out["coordinates_rounded"])
        self.assertEqual(out["rounding_decimals"], 2)
        coarse = export_record(hypothesized(), decimals=0)
        self.assertEqual((coarse["latitude"], coarse["longitude"]), (-41.0, 80.0))
        one = export_record(hypothesized(), decimals=1)
        self.assertEqual((one["latitude"], one["longitude"]), (-40.6, 80.3))

    def test_share_exact_keeps_hypothesized_coordinates_exact(self):
        out = export_record(hypothesized(share_exact=True), decimals=0)
        self.assertEqual((out["latitude"], out["longitude"]), (-40.567891, 80.254321))
        self.assertFalse(out["coordinates_rounded"])
        self.assertIsNone(out["rounding_decimals"])

    def test_sourced_coordinates_keep_their_source_precision(self):
        for kind in (DOCUMENTED, LAST_CONFIRMED):
            out = export_record(documented(kind=kind), decimals=0)
            self.assertEqual((out["latitude"], out["longitude"]), (-35.123456, -120.654321))
            self.assertFalse(out["coordinates_rounded"])
            self.assertEqual(out["kind"], kind)

    def test_rounding_never_exports_negative_zero(self):
        out = export_record(hypothesized(latitude=-0.04, longitude=-120.654321), decimals=1)
        self.assertEqual(out["latitude"], 0.0)
        self.assertEqual(math.copysign(1.0, out["latitude"]), 1.0)

    def test_invalid_record_or_precision_is_not_exported(self):
        with self.assertRaises(PositionRecordError):
            export_record(hypothesized(counterevidence=(), limits_note=""))
        for decimals in (-1, 11, 2.0, True, "2"):
            with self.assertRaises(PositionRecordError):
                export_record(hypothesized(), decimals=decimals)

    def test_export_is_deterministic(self):
        records = [documented(), hypothesized(), hypothesized(record_id="SYNTHETIC-HYP-2", share_exact=True)]
        first = export_json(records, decimals=2)
        second = export_json([replace(record) for record in records], decimals=2)
        self.assertEqual(first, second)
        loaded = json.loads(first)
        self.assertEqual([item["record_id"] for item in loaded], ["SYNTHETIC-DOC-1", "SYNTHETIC-HYP-1", "SYNTHETIC-HYP-2"])
        self.assertEqual(list(loaded[0].keys()), sorted(loaded[0].keys()))
        self.assertEqual(export_record(hypothesized()), export_record(hypothesized()))


if __name__ == "__main__":
    unittest.main()
