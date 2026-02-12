import argparse
import datetime as dt
import re
import sys

import tomli

DATA_FILE_DEFAULT = "data.toml"

# Fallback types used when no [categories] section exists in data.toml
_FALLBACK_TYPES = {
    "bakery",
    "restaurant",
    "cafe",
    "bar",
    "bookstore",
    "bikeshop",
    "store",
}


def extract_allowed_types(data):
    """Derive allowed business types from the [categories] section of data.

    Each broad category has a 'subcategories' dict whose keys are the valid types.
    Falls back to _FALLBACK_TYPES when categories are absent.
    """
    categories = data.get("categories", {})
    if not categories:
        return _FALLBACK_TYPES
    types = set()
    for cat in categories.values():
        if isinstance(cat, dict) and "subcategories" in cat:
            types.update(cat["subcategories"].keys())
    return types if types else _FALLBACK_TYPES

DAY_NAMES = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "default",
}

TIME_RANGE_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")
ID_RE = re.compile(r"^[a-z0-9_-]+$")


def _add_error(errors, path, message):
    errors.append(f"{path}: {message}")


def _add_warning(warnings, path, message):
    warnings.append(f"{path}: {message}")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_time_range(value, path, errors):
    if value == "Closed":
        return
    match = TIME_RANGE_RE.match(value)
    if not match:
        _add_error(errors, path, "expected 'HH:MM-HH:MM' or 'Closed'")
        return
    start, end = value.split("-")
    sh, sm = start.split(":")
    eh, em = end.split(":")
    start_minutes = int(sh) * 60 + int(sm)
    end_minutes = int(eh) * 60 + int(em)
    if start_minutes >= end_minutes:
        _add_error(errors, path, "start time must be before end time")


def _validate_hours_table(hours, path, errors):
    if not isinstance(hours, dict):
        _add_error(errors, path, "hours must be a table")
        return
    for key, value in hours.items():
        if key not in DAY_NAMES:
            _add_error(errors, f"{path}.{key}", "invalid day name")
            continue
        if not isinstance(value, str):
            _add_error(errors, f"{path}.{key}", "hours must be a string")
            continue
        _validate_time_range(value, f"{path}.{key}", errors)


def _validate_holiday_hours_table(holiday_hours, path, errors):
    if not isinstance(holiday_hours, dict):
        _add_error(errors, path, "holiday_hours must be a table")
        return
    for key, value in holiday_hours.items():
        try:
            dt.date.fromisoformat(key)
        except ValueError:
            _add_error(errors, f"{path}.{key}", "holiday date must be YYYY-MM-DD")
            continue
        if not isinstance(value, str):
            _add_error(errors, f"{path}.{key}", "hours must be a string")
            continue
        _validate_time_range(value, f"{path}.{key}", errors)


def _validate_lat_long(item, path, errors):
    lat = item.get("lat")
    lng = item.get("long")
    if lat is None or lng is None:
        return
    if not _is_number(lat) or not _is_number(lng):
        _add_error(errors, path, "lat/long must be numbers")
        return
    if not (-90 <= lat <= 90):
        _add_error(errors, f"{path}.lat", "lat out of range (-90 to 90)")
    if not (-180 <= lng <= 180):
        _add_error(errors, f"{path}.long", "long out of range (-180 to 180)")


def validate_data(data):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        _add_error(errors, "data", "root must be a TOML table")
        return errors, warnings

    allowed_types = extract_allowed_types(data)

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        _add_error(errors, "title", "must be a non-empty string")

    map_defaults = data.get("map_defaults")
    if map_defaults is None:
        _add_warning(warnings, "map_defaults", "missing map_defaults")
    elif not isinstance(map_defaults, dict):
        _add_error(errors, "map_defaults", "must be a table")
    else:
        for key in ("lat", "long", "zoom"):
            if key not in map_defaults:
                _add_error(errors, f"map_defaults.{key}", "is required")
            elif not _is_number(map_defaults[key]):
                _add_error(errors, f"map_defaults.{key}", "must be a number")
        if "min_zoom" in map_defaults and not _is_number(map_defaults["min_zoom"]):
            _add_error(errors, "map_defaults.min_zoom", "must be a number")
        if "max_bounds" in map_defaults:
            bounds = map_defaults["max_bounds"]
            if (
                not isinstance(bounds, list)
                or len(bounds) != 2
                or any(not isinstance(pair, list) or len(pair) != 2 for pair in bounds)
            ):
                _add_error(errors, "map_defaults.max_bounds", "must be [[lat, long], [lat, long]]")

    businesses = data.get("businesses", [])
    if not isinstance(businesses, list):
        _add_error(errors, "businesses", "must be an array")
        businesses = []

    locations = data.get("locations", [])
    if not isinstance(locations, list):
        _add_error(errors, "locations", "must be an array")
        locations = []

    seen_ids = {}

    def track_id(item_id, path):
        if item_id in seen_ids:
            _add_error(errors, path, f"duplicate id also used at {seen_ids[item_id]}")
        else:
            seen_ids[item_id] = path

    for idx, business in enumerate(businesses):
        path = f"businesses[{idx}]"
        if not isinstance(business, dict):
            _add_error(errors, path, "must be a table")
            continue

        biz_id = business.get("id")
        if not isinstance(biz_id, str) or not biz_id.strip():
            _add_error(errors, f"{path}.id", "must be a non-empty string")
        else:
            if not ID_RE.match(biz_id):
                _add_error(errors, f"{path}.id", "use lowercase letters, digits, '_' or '-' only")
            track_id(biz_id, f"{path}.id")

        if not isinstance(business.get("name"), str) or not business["name"].strip():
            _add_error(errors, f"{path}.name", "must be a non-empty string")

        biz_type = business.get("type")
        if isinstance(biz_type, str):
            types = [biz_type]
        elif isinstance(biz_type, list):
            types = biz_type
        else:
            types = []
        if not types:
            _add_error(errors, f"{path}.type", "must be a string or non-empty array")
        else:
            for t in types:
                if not isinstance(t, str):
                    _add_error(errors, f"{path}.type", "type values must be strings")
                    break
                if t not in allowed_types:
                    _add_error(errors, f"{path}.type", f"unsupported type '{t}'")

        if "address" not in business and ("lat" not in business or "long" not in business):
            _add_error(errors, path, "requires address or lat/long")

        if "phone" in business and not isinstance(business["phone"], str):
            _add_error(errors, f"{path}.phone", "must be a string")

        if "description" in business and not isinstance(business["description"], str):
            _add_error(errors, f"{path}.description", "must be a string")

        _validate_lat_long(business, path, errors)

        if "hours" in business:
            _validate_hours_table(business["hours"], f"{path}.hours", errors)
        if "holiday_hours" in business:
            _validate_holiday_hours_table(business["holiday_hours"], f"{path}.holiday_hours", errors)

    for idx, location in enumerate(locations):
        path = f"locations[{idx}]"
        if not isinstance(location, dict):
            _add_error(errors, path, "must be a table")
            continue

        loc_id = location.get("id")
        if not isinstance(loc_id, str) or not loc_id.strip():
            _add_error(errors, f"{path}.id", "must be a non-empty string")
        else:
            if not ID_RE.match(loc_id):
                _add_error(errors, f"{path}.id", "use lowercase letters, digits, '_' or '-' only")
            track_id(loc_id, f"{path}.id")

        if not isinstance(location.get("name"), str) or not location["name"].strip():
            _add_error(errors, f"{path}.name", "must be a non-empty string")

        if "address" not in location and ("lat" not in location or "long" not in location):
            _add_error(errors, path, "requires address or lat/long")

        _validate_lat_long(location, path, errors)

        if "zoom" in location and not _is_number(location["zoom"]):
            _add_error(errors, f"{path}.zoom", "must be a number")

    if not businesses:
        _add_warning(warnings, "businesses", "no businesses listed")
    if not locations:
        _add_warning(warnings, "locations", "no locations listed")

    return errors, warnings


def load_data(path):
    with open(path, "rb") as f:
        return tomli.load(f)


def main():
    parser = argparse.ArgumentParser(description="Validate data.toml structure and values.")
    parser.add_argument("path", nargs="?", default=DATA_FILE_DEFAULT, help="Path to data.toml")
    args = parser.parse_args()

    try:
        data = load_data(args.path)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.path}")
        return 1
    except tomli.TOMLDecodeError as exc:
        print(f"ERROR: invalid TOML: {exc}")
        return 1

    errors, warnings = validate_data(data)

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1

    print(f"Validation passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
