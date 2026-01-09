import json
import os
import urllib.request
import urllib.parse
import time
import ssl

CACHE_FILE = 'geocoding_cache.json'

def get_ssl_context():
    # Attempt to use a more permissive SSL context if the default one fails
    # This is often needed on macOS with default Python installations
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def geocode(address):
    cache = load_cache()
    if address in cache:
        return cache[address]

    print(f"Geocoding address: {address}")
    # Nominatim requires a User-Agent.
    headers = {'User-Agent': 'MappingProjectGeocoder/1.0'}
    encoded_address = urllib.parse.quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"

    try:
        req = urllib.request.Request(url, headers=headers)
        # Try with default context first, then fall back to permissive context
        try:
            response = urllib.request.urlopen(req)
        except ssl.SSLCertVerificationError:
            print("SSL verification failed, trying with permissive context...")
            response = urllib.request.urlopen(req, context=get_ssl_context())
        except Exception:
             # some other error, try permissive anyway as a last resort if it looks like SSL
             response = urllib.request.urlopen(req, context=get_ssl_context())

        with response:
            data = json.loads(response.read().decode())
            if data:
                result = {
                    'lat': float(data[0]['lat']),
                    'long': float(data[0]['lon'])
                }
                cache[address] = result
                save_cache(cache)
                # Respect Nominatim usage policy (1 request per second)
                time.sleep(1)
                return result
            else:
                print(f"No results found for address: {address}")
                return None
    except Exception as e:
        print(f"Error during geocoding {address}: {e}")
        return None

def process_data_with_geocoding(data):
    """
    Updates data in-place by filling missing lat/long from address.
    """
    updated = False
    for category in ['businesses', 'locations']:
        if category in data:
            for item in data[category]:
                if ('lat' not in item or 'long' not in item) and 'address' in item:
                    coords = geocode(item['address'])
                    if coords:
                        item['lat'] = coords['lat']
                        item['long'] = coords['long']
                        updated = True
    return updated
