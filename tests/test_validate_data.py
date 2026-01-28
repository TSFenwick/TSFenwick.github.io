import unittest

from validate_data import validate_data


class TestValidateData(unittest.TestCase):
    def test_valid_data(self):
        data = {
            "title": "Test Site",
            "map_defaults": {"lat": 37.7, "long": -122.5, "zoom": 14},
            "businesses": [
                {
                    "id": "coffee_shop",
                    "name": "Coffee Shop",
                    "type": ["cafe"],
                    "address": "123 Main St, San Francisco, CA 94122",
                    "hours": {"default": "08:00-18:00"},
                }
            ],
            "locations": [
                {"id": "park", "name": "Local Park", "lat": 37.71, "long": -122.51}
            ],
        }
        errors, warnings = validate_data(data)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_invalid_type_and_duplicate_id(self):
        data = {
            "title": "Test Site",
            "map_defaults": {"lat": 37.7, "long": -122.5, "zoom": 14},
            "businesses": [
                {
                    "id": "dup_id",
                    "name": "Shop A",
                    "type": ["invalid_type"],
                    "address": "123 Main St, San Francisco, CA 94122",
                }
            ],
            "locations": [
                {"id": "dup_id", "name": "Location A", "lat": 37.71, "long": -122.51}
            ],
        }
        errors, _warnings = validate_data(data)
        self.assertTrue(any("unsupported type" in err for err in errors))
        self.assertTrue(any("duplicate id" in err for err in errors))

    def test_invalid_hours(self):
        data = {
            "title": "Test Site",
            "map_defaults": {"lat": 37.7, "long": -122.5, "zoom": 14},
            "businesses": [
                {
                    "id": "bad_hours",
                    "name": "Late Shop",
                    "type": ["store"],
                    "address": "123 Main St, San Francisco, CA 94122",
                    "hours": {"monday": "18:00-08:00"},
                }
            ],
            "locations": [],
        }
        errors, _warnings = validate_data(data)
        self.assertTrue(any("start time must be before end time" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
