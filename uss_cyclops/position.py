"""Position records that keep documented positions apart from hypotheses.

A record is documented (a cited source states the position), last_confirmed (a cited source states the last confirmed
position) or hypothesized (an inference no source states). A hypothesized record must say what argues against it or
limits it, can never be relabelled as documented or last_confirmed, and is rounded on export unless the record itself
sets share_exact. Sourced coordinates are exported exactly as stated. Standard library only.
"""

import json
import math
from dataclasses import dataclass, replace

DOCUMENTED = "documented"
LAST_CONFIRMED = "last_confirmed"
HYPOTHESIZED = "hypothesized"
KINDS = (DOCUMENTED, LAST_CONFIRMED, HYPOTHESIZED)
SOURCED_KINDS = (DOCUMENTED, LAST_CONFIRMED)
TIME_PRECISIONS = ("year", "month", "day", "hour", "minute")
MAX_EXPORT_DECIMALS = 10


class PositionRecordError(ValueError):
    """A record broke one or more rules; .errors lists every problem found."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


@dataclass(frozen=True)
class PositionRecord:
    record_id: str
    kind: str
    latitude: float
    longitude: float
    uncertainty_nm: float = None
    source_id: str = None
    page: str = None
    time: str = None
    time_precision: str = None
    evidence: tuple = ()
    counterevidence: tuple = ()
    limits_note: str = ""
    share_exact: bool = False


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_text(value):
    return isinstance(value, str) and value.strip() != ""


def _is_page(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value >= 1
    return _is_text(value)


def _is_text_list(value):
    return isinstance(value, (list, tuple)) and all(_is_text(item) for item in value)


def validate_record(record):
    """Return a list of every rule the record breaks; an empty list means it is valid."""
    errors = []
    if not _is_text(record.record_id):
        errors.append("record_id must be a non-empty string")
    if record.kind not in KINDS:
        errors.append("kind must be one of %s, got %r" % (", ".join(KINDS), record.kind))
    if not _is_number(record.latitude) or not -90 <= record.latitude <= 90:
        errors.append("latitude must be a finite number from -90 to 90")
    if not _is_number(record.longitude) or not -180 <= record.longitude <= 180:
        errors.append("longitude must be a finite number from -180 to 180")
    if record.uncertainty_nm is None:
        errors.append("uncertainty_nm is required for every kind")
    elif not _is_number(record.uncertainty_nm) or record.uncertainty_nm < 0:
        errors.append("uncertainty_nm must be a finite number of nautical miles, 0 or more")
    if record.kind in SOURCED_KINDS:
        if not _is_text(record.source_id):
            errors.append("%s records need a source_id" % record.kind)
        if not _is_page(record.page):
            errors.append("%s records need a page" % record.kind)
    if not _is_text_list(record.evidence):
        errors.append("evidence must be a list of non-empty strings")
    if not _is_text_list(record.counterevidence):
        errors.append("counterevidence must be a list of non-empty strings")
    if not isinstance(record.limits_note, str):
        errors.append("limits_note must be a string")
    if record.kind == HYPOTHESIZED:
        has_counter = _is_text_list(record.counterevidence) and len(record.counterevidence) > 0
        if not has_counter and not _is_text(record.limits_note):
            errors.append("hypothesized records need counterevidence or a limits_note")
    if record.time is not None:
        if not _is_text(record.time):
            errors.append("time must be a non-empty string when given")
        if record.time_precision not in TIME_PRECISIONS:
            errors.append("time_precision must be one of %s when time is given" % ", ".join(TIME_PRECISIONS))
    elif record.time_precision is not None:
        errors.append("time_precision needs a time")
    if not isinstance(record.share_exact, bool):
        errors.append("share_exact must be True or False")
    return errors


def check_record(record):
    """Return the record if it is valid, otherwise raise PositionRecordError."""
    errors = validate_record(record)
    if errors:
        raise PositionRecordError(errors)
    return record


def reclassify(record, new_kind):
    """Return a copy with a new kind; a hypothesis can never become a documented or last-confirmed position."""
    if record.kind == HYPOTHESIZED and new_kind in SOURCED_KINDS:
        raise PositionRecordError(
            ["a hypothesized record can never become %s; make a new sourced record instead" % new_kind]
        )
    return check_record(replace(record, kind=new_kind))


def _round_coordinate(value, decimals):
    rounded = round(float(value), decimals)
    return 0.0 if rounded == 0 else rounded


def export_record(record, decimals=2):
    """Export a valid record as a plain dict.

    Hypothesized coordinates are rounded to `decimals` places unless the record has share_exact True. Documented and
    last_confirmed coordinates keep the precision their source gave.
    """
    if not isinstance(decimals, int) or isinstance(decimals, bool) or not 0 <= decimals <= MAX_EXPORT_DECIMALS:
        raise PositionRecordError(["decimals must be an integer from 0 to %d" % MAX_EXPORT_DECIMALS])
    check_record(record)
    rounded = record.kind == HYPOTHESIZED and not record.share_exact
    latitude = _round_coordinate(record.latitude, decimals) if rounded else record.latitude
    longitude = _round_coordinate(record.longitude, decimals) if rounded else record.longitude
    return {
        "record_id": record.record_id,
        "kind": record.kind,
        "latitude": latitude,
        "longitude": longitude,
        "uncertainty_nm": record.uncertainty_nm,
        "source_id": record.source_id,
        "page": record.page,
        "time": record.time,
        "time_precision": record.time_precision,
        "evidence": list(record.evidence),
        "counterevidence": list(record.counterevidence),
        "limits_note": record.limits_note,
        "share_exact": record.share_exact,
        "coordinates_rounded": rounded,
        "rounding_decimals": decimals if rounded else None,
    }


def export_json(records, decimals=2):
    """Export records as deterministic JSON text (sorted keys, fixed separators, input order kept)."""
    return json.dumps([export_record(record, decimals) for record in records], sort_keys=True, separators=(",", ":"))
