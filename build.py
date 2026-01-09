# /// script
# dependencies = [
#   "tomli",
# ]
# ///

import tomli
import json
import os

# Configuration
TOML_FILE = 'data.toml'
OUTPUT_FILE = 'index.html'

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
        
        /* Layout */
        header {{ background: #fff; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1000; display: flex; gap: 10px; overflow-x: auto; }}
        #map {{ flex-grow: 1; z-index: 1; }}
        #list-view {{ display: none; flex-grow: 1; overflow-y: auto; background: var(--bg); padding: 10px; }}
        
        /* Controls */
        select, button {{ padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; font-size: 14px; cursor: pointer; }}
        button.active {{ background: var(--primary); color: white; border-color: var(--primary); }}
        
        /* Business Card (List View & Popup) */
        .biz-card {{ background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .biz-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
        .biz-name {{ margin: 0; font-size: 1.1em; font-weight: bold; }}
        .biz-type {{ font-size: 0.8em; text-transform: uppercase; color: #666; background: #eee; padding: 2px 6px; border-radius: 4px; }}
        .biz-status {{ font-weight: bold; font-size: 0.9em; }}
        .open {{ color: green; }}
        .closed {{ color: red; }}
        .biz-actions {{ margin-top: 10px; display: flex; gap: 10px; }}
        .btn-link {{ text-decoration: none; color: var(--primary); font-size: 0.9em; font-weight: 500; }}
        
        /* Leaflet Tweaks */
        .leaflet-popup-content-wrapper {{ border-radius: 8px; padding: 0; }}
        .leaflet-popup-content {{ margin: 0; width: 280px !important; }}
        .popup-card {{ border: none; box-shadow: none; margin: 0; }}
        
        /* Custom Marker Icons */
        .custom-icon {{ text-align: center; line-height: 30px; font-size: 20px; background: white; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</head>
<body>

<header>
        <select id="filter-type">
            <option value="all">All Places</option>
        </select>
        <button id="btn-map" class="active">Map</button>
    <button id="btn-list">List</button>
    <button id="btn-loc">📍 Me</button>
</header>

<div id="map"></div>
<div id="list-view"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
    // --- 1. PRE-SEEDED DATA ---
    const rawData = {json_data};
    const businesses = rawData.businesses;

    // --- 2. STATE ---
    let map, userMarker;
    let currentView = 'map'; // 'map' or 'list'
    let currentFilter = 'all';
    let userLoc = null; 
    let markers = [];

    // --- 3. LOGIC: Time & Open Status ---
    function getOpenStatus(b) {{
        const now = new Date();
        const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
        const dayName = days[now.getDay()];
        const dateString = now.toISOString().split('T')[0]; // YYYY-MM-DD format

        // Check Holidays first
        let hoursStr = null;
        if (b.holiday_hours && b.holiday_hours[dateString]) {{
            hoursStr = b.holiday_hours[dateString];
        }} else if (b.hours) {{
            hoursStr = b.hours[dayName] || b.hours['default'];
        }}

        if (!hoursStr || hoursStr === 'Closed') return {{ isOpen: false, text: 'Closed today' }};

        // Parse "07:00-16:00"
        const [start, end] = hoursStr.split('-');
        const [sh, sm] = start.split(':').map(Number);
        const [eh, em] = end.split(':').map(Number);
        
        const nowMinutes = now.getHours() * 60 + now.getMinutes();
        const startMinutes = sh * 60 + sm;
        const endMinutes = eh * 60 + em;

        const isOpen = nowMinutes >= startMinutes && nowMinutes < endMinutes;
        return {{ 
            isOpen: isOpen, 
            text: isOpen ? `Open until ${{end}}` : `Closed (Opens ${{start}})`
        }};
    }}

    // --- 4. RENDER FUNCTIONS ---
    
    // Icon Mapping (Emoji fallback)
    function getIconHtml(type) {{
        const icons = {{ 'cafe': '☕', 'restaurant': '🍔', 'store': '🛍️', 'bar': '🍺' }};
        return icons[type] || '📍';
    }}

    function createCardHTML(b) {{
            const status = getOpenStatus(b);
            const statusClass = status.isOpen ? 'open' : 'closed';
            const typeDisplay = Array.isArray(b.type) ? b.type.join(' & ') : b.type;
    
            return `
                <div class="biz-card popup-card">
                    <div class="biz-header">
                        <span class="biz-name">${{b.name}}</span>
                        <span class="biz-type">${{typeDisplay}}</span>
                    </div>
                    <div class="biz-status ${{statusClass}}">${{status.text}}</div>
                <p>${{b.description}}</p>
                <div class="biz-actions">
                     <a href="https://www.google.com/maps/dir/?api=1&destination=${{b.lat}},${{b.long}}" target="_blank" class="btn-link">Navigate ↗</a>
                     ${{b.phone ? `<a href="tel:${{b.phone}}" class="btn-link">Call</a>` : ''}}
                </div>
            </div>
        `;
    }}

    function renderList(data) {{
        const container = document.getElementById('list-view');
        container.innerHTML = '';
        if(data.length === 0) container.innerHTML = '<p style="text-align:center; margin-top:20px;">No results found.</p>';
        
        data.forEach(b => {{
            container.innerHTML += createCardHTML(b);
        }});
    }}

        function renderMap(data) {{
            // Clear layers
            markers.forEach(m => map.removeLayer(m));
            markers = [];

            data.forEach(b => {{
                const primaryType = Array.isArray(b.type) ? b.type[0] : b.type;
                const icon = L.divIcon({{
                    className: 'custom-icon',
                    html: getIconHtml(primaryType),
                    iconSize: [30, 30],
                iconAnchor: [15, 15] // Center the icon
            }});

            const marker = L.marker([b.lat, b.long], {{ icon: icon }}).addTo(map);
            marker.bindPopup(createCardHTML(b));
            markers.push(marker);
        }});
    }}

        function updateApp() {{
            // Filter Data
            let filtered = businesses;
            if (currentFilter !== 'all') {{
                filtered = businesses.filter(b => {{
                    if (Array.isArray(b.type)) {{
                        return b.type.includes(currentFilter);
                    }}
                    return b.type === currentFilter;
                }});
            }}

            // If we have user location, calculate distance
        if (userLoc) {{
             filtered.forEach(b => {{
                 b.distance = map.distance(userLoc, [b.lat, b.long]); 
             }});
             // Sort by distance
             filtered.sort((a, b) => a.distance - b.distance);
        }}

        if (currentView === 'map') renderMap(filtered);
        else renderList(filtered);
    }}

    // --- 5. INITIALIZATION ---
    window.onload = function() {{
        // Generate Dynamic Filters
        const filterSelect = document.getElementById('filter-type');
        const allTypes = new Set();
        businesses.forEach(b => {{
            if (Array.isArray(b.type)) {{
                b.type.forEach(t => allTypes.add(t));
            }} else {{
                allTypes.add(b.type);
            }}
        }});

        Array.from(allTypes).sort().forEach(type => {{
            const opt = document.createElement('option');
            opt.value = type;
            opt.textContent = type.charAt(0).toUpperCase() + type.slice(1) + 's';
            filterSelect.appendChild(opt);
        }});

        // Parse URL for Start Location
        const params = new URLSearchParams(window.location.search);
        const lat = parseFloat(params.get('lat')) || 37.7749;
        const lng = parseFloat(params.get('lng')) || -122.4194;
        const zoom = parseInt(params.get('zoom')) || 15;

        // Init Map
        map = L.map('map').setView([lat, lng], zoom);
        
        // Lightweight Tiles
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            maxZoom: 20
        }}).addTo(map);

        // Initial Render
        updateApp();

        // --- EVENTS ---
        
        // Toggle Map/List
        document.getElementById('btn-map').onclick = () => {{
            document.getElementById('map').style.display = 'block';
            document.getElementById('list-view').style.display = 'none';
            document.getElementById('btn-map').classList.add('active');
            document.getElementById('btn-list').classList.remove('active');
            currentView = 'map';
            updateApp();
        }};
        
        document.getElementById('btn-list').onclick = () => {{
            document.getElementById('map').style.display = 'none';
            document.getElementById('list-view').style.display = 'block';
            document.getElementById('btn-list').classList.add('active');
            document.getElementById('btn-map').classList.remove('active');
            currentView = 'list';
            updateApp();
        }};

        // Filter
        document.getElementById('filter-type').onchange = (e) => {{
            currentFilter = e.target.value;
            updateApp();
        }};

        // Live Location
        document.getElementById('btn-loc').onclick = () => {{
            if (!navigator.geolocation) return alert('Geolocation not supported');
            
            // Show loading state (optional)
            document.getElementById('btn-loc').textContent = '⏳';

            navigator.geolocation.getCurrentPosition(pos => {{
                const {{ latitude, longitude }} = pos.coords;
                userLoc = [latitude, longitude];
                
                // Add/Update User Marker
                if (userMarker) map.removeLayer(userMarker);
                userMarker = L.circleMarker(userLoc, {{ radius: 8, color: 'blue', fillColor: '#2a81cb', fillOpacity: 1 }}).addTo(map);
                
                // Center Map
                map.setView(userLoc, 16);
                
                document.getElementById('btn-loc').textContent = '📍 Me';
                
                // Update views (trigger sorting)
                updateApp();
            }}, err => {{
                console.error(err);
                alert('Could not get location.');
                document.getElementById('btn-loc').textContent = '📍 Me';
            }});
        }};
    }};
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
    
    # 2. Convert Data to JSON string
    json_data = json.dumps(data, ensure_ascii=False)

    print(json_data)
    # 3. Inject into HTML
    print("Injecting data into HTML...")
    final_html = HTML_TEMPLATE.format(
        site_title=data.get('title', 'Guide'),
        json_data=json_data
    )
    
    # 4. Write Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"Build complete! Open {OUTPUT_FILE} to view your site.")

if __name__ == "__main__":
    build()
