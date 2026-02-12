import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
from geocoding import geocode, process_data_with_geocoding, load_cache, save_cache

class TestGeocoding(unittest.TestCase):

    def setUp(self):
        # Mock the cache file path to avoid messing with real cache
        self.cache_patcher = patch('geocoding.CACHE_FILE', 'test_geocoding_cache.json')
        self.mock_cache_file = self.cache_patcher.start()

    def tearDown(self):
        self.cache_patcher.stop()
        if os.path.exists('test_geocoding_cache.json'):
            os.remove('test_geocoding_cache.json')

    @patch('builtins.open', new_callable=mock_open, read_data='{"cached addr": {"lat": 1.0, "long": 2.0}}')
    @patch('os.path.exists')
    def test_load_cache(self, mock_exists, mock_file):
        mock_exists.return_value = True
        cache = load_cache()
        self.assertEqual(cache, {"cached addr": {"lat": 1.0, "long": 2.0}})

    @patch('geocoding.load_cache')
    @patch('geocoding.save_cache')
    @patch('urllib.request.urlopen')
    def test_geocode_success(self, mock_urlopen, mock_save_cache, mock_load_cache):
        # Mock load_cache to return empty dict
        mock_load_cache.return_value = {}
        
        # Mock network response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([{'lat': '12.34', 'lon': '56.78'}]).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        cache = {}
        result = geocode("New York", cache=cache)
        
        self.assertEqual(result, {'lat': 12.34, 'long': 56.78})
        self.assertIn("New York", cache)

    @patch('geocoding.load_cache')
    def test_geocode_cached(self, mock_load_cache):
        mock_load_cache.return_value = {"Cached Place": {"lat": 10.0, "long": 20.0}}
        
        result = geocode("Cached Place")
        self.assertEqual(result, {"lat": 10.0, "long": 20.0})

    @patch('geocoding.geocode')
    def test_process_data_with_geocoding(self, mock_geocode):
        data = {
            'businesses': [
                {'name': 'B1', 'address': 'Addr1'}, # Missing lat/long
                {'name': 'B2', 'lat': 1, 'long': 1} # Has lat/long
            ],
            'locations': []
        }
        
        mock_geocode.return_value = {'lat': 5.0, 'long': 6.0}
        
        updated = process_data_with_geocoding(data)
        
        self.assertTrue(updated)
        self.assertEqual(data['businesses'][0]['lat'], 5.0)
        self.assertEqual(data['businesses'][0]['long'], 6.0)
        # Should verify geocode was called only for B1
        mock_geocode.assert_called_once_with('Addr1', cache={})

if __name__ == '__main__':
    unittest.main()
