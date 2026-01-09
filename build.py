# /// script
# dependencies = [
#   "tomli",
#   "tomli-w",
# ]
# ///

import tomli
import tomli_w
import json
import subprocess
import os
import re
from geocoding import process_data_with_geocoding

# Configuration
TOML_FILE = 'data.toml'
ENRICHED_TOML_FILE = 'data_enriched.toml'
OUTPUT_FILE = 'index.html'
OUTPUT_FILE_UNMIN = 'index_unminified.html'

def minify_code(content):
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    # Remove CSS/JS block comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove leading/trailing whitespace on lines
    content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)
    # Remove empty lines
    content = re.sub(r'\n+', '', content)
    return content

# The HTML Template
# We use a Python f-string to inject the JSON directly into the JS variable.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title}</title>
    <style>
        /* CRITICAL CSS - INLINED FOR SPEED */
        :root {{ --primary: #007bff; --bg: #f4f4f4; }}
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; height: 100vh; display: flex; flex-direction: column; }}
        header {{ background: #fff; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1000; position: relative; display: flex; gap: 10px; flex-wrap: wrap; }}
        #map {{ flex-grow: 1; z-index: 1; }}
        #list-view {{ display: none; flex-grow: 1; overflow-y: auto; background: var(--bg); padding: 10px; }}
        select, button {{ padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; font-size: 14px; cursor: pointer; }}
        button.active {{ background: var(--primary); color: white; border-color: var(--primary); }}
        .biz-card {{ background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .biz-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
        .biz-name {{ margin: 0; font-size: 1.1em; font-weight: bold; }}
        .biz-type {{ font-size: 0.8em; text-transform: uppercase; color: #666; background: #eee; padding: 2px 6px; border-radius: 4px; }}
        .biz-status {{ font-weight: bold; font-size: 0.9em; }}
        .open {{ color: green; }}
        .closed {{ color: red; }}
        .biz-actions {{ margin-top: 10px; display: flex; gap: 10px; }}
        .btn-link {{ text-decoration: none; color: var(--primary); font-size: 0.9em; font-weight: 500; }}
        .leaflet-popup-content-wrapper {{ border-radius: 8px; padding: 0; }}
        .leaflet-popup-content {{ margin: 0; width: 280px !important; }}
        .popup-card {{ border: none; box-shadow: none; margin: 0; }}
        .custom-icon {{ text-align: center; line-height: 30px; font-size: 20px; background: white; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        /* Marker Cluster Styles */
        .marker-cluster {{ background-clip: padding-box; border-radius: 50%; display: flex; align-items: center; justify-content: center; }}
        .marker-cluster div {{ width: 30px; height: 30px; margin: 5px; text-align: center; border-radius: 50%; font: 12px "Helvetica Neue", Arial, Helvetica, sans-serif; font-weight: bold; display: flex; align-items: center; justify-content: center; }}
        .marker-cluster-small {{ background-color: rgba(110, 204, 57, 0.6); }}
        .marker-cluster-small div {{ background-color: rgba(110, 204, 57, 0.8); color: white; }}
        .marker-cluster-medium {{ background-color: rgba(240, 194, 12, 0.6); }}
        .marker-cluster-medium div {{ background-color: rgba(240, 194, 12, 0.8); color: white; }}
        .marker-cluster-large {{ background-color: rgba(241, 128, 23, 0.6); }}
        .marker-cluster-large div {{ background-color: rgba(241, 128, 23, 0.8); color: white; }}
        .stacked-icon {{ position: relative; text-align: center; line-height: 30px; font-size: 20px; background: white; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .stacked-icon .stack-count {{ position: absolute; top: -8px; right: -8px; background: #ff4444; color: white; border-radius: 50%; width: 18px; height: 18px; font-size: 11px; font-weight: bold; line-height: 18px; text-align: center; border: 2px solid white; }}
        .multi-icon-cluster {{ background: white; border-radius: 20px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4px 6px; }}
        .multi-icon-cluster .cluster-icons {{ display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 2px; }}
        .multi-icon-cluster .cluster-type-icon {{ font-size: 16px; line-height: 1; }}
        .multi-icon-cluster .cluster-count {{ font-size: 10px; font-weight: bold; color: #666; margin-top: 1px; }}
        .cluster-popup-content {{ max-height: 300px; overflow-y: auto; }}
        .cluster-popup-content .biz-card {{ border-bottom: 1px solid #eee; margin-bottom: 10px; padding-bottom: 10px; }}
        .cluster-popup-content .biz-card:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        /* Hierarchical Dropdown Styles */
        .dropdown {{ position: relative; min-width: 140px; }}
        .dropdown-selected {{ padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 8px; white-space: nowrap; }}
        .dropdown-selected:hover {{ border-color: #999; }}
        .dropdown-text {{ display: flex; align-items: center; gap: 4px; }}
        .dropdown-arrow {{ font-size: 10px; color: #666; transition: transform 0.2s; }}
        .dropdown.open .dropdown-arrow {{ transform: rotate(180deg); }}
        .dropdown-options {{ display: none; position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ccc; border-radius: 4px; margin-top: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 10000; max-height: 300px; overflow-y: auto; min-width: 180px; }}
        .dropdown.open .dropdown-options {{ display: block; }}
        .dropdown-item {{ padding: 10px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; }}
        .dropdown-item:hover {{ background: #f5f5f5; }}
        .item-emoji {{ font-size: 16px; width: 24px; text-align: center; }}
        .item-label {{ flex: 1; }}
        .category-header {{ font-weight: 500; }}
        .category-header .item-label {{ flex: 1; }}
        .expand-toggle {{ font-size: 10px; color: #666; padding: 4px 8px; cursor: pointer; transition: transform 0.2s; }}
        .expand-toggle:hover {{ color: #333; background: #eee; border-radius: 4px; }}
        .expand-toggle.expanded {{ color: var(--primary); }}
        .subcategory-list {{ display: none; background: #fafafa; }}
        .subcategory-list.expanded {{ display: block; }}
        .subcategory-item {{ padding-left: 28px; font-size: 13px; }}
        .subcategory-item .item-emoji {{ font-size: 14px; }}
        .dropdown-category {{ border-bottom: 1px solid #eee; }}
        .dropdown-category:last-child {{ border-bottom: none; }}
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
</head>
<body>
<header>
    <div id="filter-dropdown" class="dropdown">
        <div class="dropdown-selected"></div>
        <div class="dropdown-options"></div>
    </div>
    <button id="btn-map" class="active">Map</button>
    <button id="btn-list">List</button>
    <button id="btn-loc">📍 Me</button>
</header>
<div id="map"></div>
<div id="list-view"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
<script>
    const rawData = {json_data};
    const businesses = rawData.businesses;
    /* JS_INJECTION_POINT */
</script>
</body>
</html>
"""

def build():
    # 1. Read TOML
    print(f"Reading {TOML_FILE}...")
    try:
        with open(TOML_FILE, "rb") as f:
            data = tomli.load(f)
    except FileNotFoundError:
        print(f"Error: {TOML_FILE} not found!")
        return

    # 1.5. Geocode addresses if lat/long are missing
    process_data_with_geocoding(data)

    # 1.6. Save enriched data
    print(f"Saving enriched data to {ENRICHED_TOML_FILE}...")
    with open(ENRICHED_TOML_FILE, "wb") as f:
        tomli_w.dump(data, f)

    # 2. Convert Data to JSON string
    # Minified JSON for production
    json_data_min = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    # Pretty JSON for dev (optional, but keep simple)
    json_data = json.dumps(data, ensure_ascii=False)

    # 2.5 Run Minification
    print("Running JS minification...")
    try:
        subprocess.run(["npm", "run", "minify"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running minification: {e}")
        return
    except FileNotFoundError:
        print("Error: npm not found. Make sure npm is installed and in your PATH.")
        return

    # 2.6 Read JS files
    try:
        with open("js/logic.js", "r", encoding="utf-8") as f:
            js_logic = f.read()
        with open("js/main.js", "r", encoding="utf-8") as f:
            js_main = f.read()
        with open("js/minified.js", "r", encoding="utf-8") as f:
            js_minified = f.read()
    except FileNotFoundError as e:
        print(f"Error reading JS files: {e}")
        return

    # 3. Inject into HTML
    print("Injecting data into HTML...")
    
    # UNMINIFIED VERSION
    formatted_html = HTML_TEMPLATE.format(
        site_title=data.get('title', 'Guide'),
        json_data=json_data
    )
    final_html_unmin = formatted_html.replace("/* JS_INJECTION_POINT */", js_logic + "\n" + js_main)

    # MINIFIED VERSION
    # Note: We must inject before stripping comments because JS_INJECTION_POINT is a comment!
    # Or we can strip "other" comments first?
    # Actually, simpler: Use formatted_html but with json_data_min
    formatted_html_min = HTML_TEMPLATE.format(
        site_title=data.get('title', 'Guide'),
        json_data=json_data_min
    )
    
    # Replace injection point with minified JS
    final_html_min = formatted_html_min.replace("/* JS_INJECTION_POINT */", js_minified)
    
    # Now minify the HTML structure
    final_html_min = minify_code(final_html_min)

    # 4. Write Output
    with open(OUTPUT_FILE_UNMIN, "w", encoding="utf-8") as f:
        f.write(final_html_unmin)
    print(f"Unminified build complete: {OUTPUT_FILE_UNMIN}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html_min)
        
    print(f"Build complete! Open {OUTPUT_FILE} to view your site.")

if __name__ == "__main__":
    build()
