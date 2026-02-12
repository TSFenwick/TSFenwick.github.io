// --- 1. UTILITIES ---
function escapeHtml(str) {
	if (!str) return "";
	return str
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}

// --- 2. STATE ---
let map, userMarker;
let currentView = "map"; // 'map' or 'list'
let currentFilter = "all";
let openNowFilter = false;
let userLoc = null;
let markers = [];
let markerClusterGroup = null;
const expandedCategories = {}; // Track which categories are expanded
let activeClusterPopup = null; // Track the currently open cluster popup

// --- 3. HIERARCHICAL DROPDOWN ---

function buildHierarchicalDropdown() {
	const container = document.getElementById("filter-dropdown");
	const selectedDisplay = container.querySelector(".dropdown-selected");
	const optionsList = container.querySelector(".dropdown-options");

	// Set the initial display
	selectedDisplay.innerHTML =
		'<span class="dropdown-text">All Places</span><span class="dropdown-arrow">▼</span>';

	// Build options list
	let html =
		'<div class="dropdown-item" data-value="all"><span class="item-emoji">📍</span><span class="item-label">All Places</span></div>';

	// Add broad categories with their subcategories
	for (const [catKey, catData] of Object.entries(categoryHierarchy)) {
		// Broad category header with expand toggle
		html += `
			<div class="dropdown-category" data-category="${catKey}">
				<div class="category-header dropdown-item" data-value="${catKey}">
					<span class="item-emoji">${catData.emoji}</span>
					<span class="item-label">${catData.label}</span>
					<span class="expand-toggle" data-category="${catKey}">▶</span>
				</div>
				<div class="subcategory-list" data-category="${catKey}">`;

		// Subcategories
		for (const [subKey, subData] of Object.entries(catData.subcategories)) {
			html += `
					<div class="dropdown-item subcategory-item" data-value="${subKey}">
						<span class="item-emoji">${subData.emoji}</span>
						<span class="item-label">${subData.label}</span>
					</div>`;
		}

		html += `
				</div>
			</div>`;
	}

	optionsList.innerHTML = html;
}

function setupDropdownEvents() {
	const container = document.getElementById("filter-dropdown");
	const selectedDisplay = container.querySelector(".dropdown-selected");
	const optionsList = container.querySelector(".dropdown-options");

	// Toggle dropdown open/close
	selectedDisplay.addEventListener("click", (e) => {
		e.stopPropagation();
		container.classList.toggle("open");
	});

	// Close dropdown when clicking outside
	document.addEventListener("click", (e) => {
		if (!container.contains(e.target)) {
			container.classList.remove("open");
		}
	});

	// Handle expand/collapse toggles
	optionsList.addEventListener("click", (e) => {
		const toggle = e.target.closest(".expand-toggle");
		if (toggle) {
			e.stopPropagation();
			const catKey = toggle.dataset.category;
			const subcatList = optionsList.querySelector(
				`.subcategory-list[data-category="${catKey}"]`,
			);

			if (expandedCategories[catKey]) {
				// Collapse
				expandedCategories[catKey] = false;
				subcatList.classList.remove("expanded");
				toggle.textContent = "▶";
				toggle.classList.remove("expanded");
			} else {
				// Expand
				expandedCategories[catKey] = true;
				subcatList.classList.add("expanded");
				toggle.textContent = "▼";
				toggle.classList.add("expanded");
			}
			return;
		}

		// Handle item selection
		const item = e.target.closest(".dropdown-item");
		if (
			(item && !item.classList.contains("category-header")) ||
			(item?.classList.contains("category-header") &&
				!e.target.closest(".expand-toggle"))
		) {
			const value = item.dataset.value;
			const emoji = item.querySelector(".item-emoji").textContent;
			const label = item.querySelector(".item-label").textContent;

			// Update the selected display
			selectedDisplay.innerHTML = `<span class="dropdown-text">${emoji} ${label}</span><span class="dropdown-arrow">▼</span>`;

			// Update filter and close dropdown
			currentFilter = value;
			container.classList.remove("open");
			updateApp();
		}
	});
}

// --- 4. RENDER FUNCTIONS ---

function createCardHTML(b, distanceMeters) {
	const status = getOpenStatus(b);
	const statusClass = status.isOpen ? "open" : "closed";
	const types = Array.isArray(b.type) ? b.type : [b.type];
	const typeLabels = types.map((t) => getDisplayLabel(t));
	const typeEmojis = types.map((t) => getIconHtml(t)).join("");
	const typeDisplay = typeLabels.join(" & ");

	const safeName = escapeHtml(b.name);
	const safeDesc = escapeHtml(b.description);
	const safePhone = escapeHtml(b.phone);
	const safeType = escapeHtml(typeDisplay);
	const safeWebsite = b.website ? escapeHtml(b.website) : "";

	let distanceHtml = "";
	if (distanceMeters != null) {
		const distText =
			distanceMeters < 1000
				? `${Math.round(distanceMeters)} m`
				: `${(distanceMeters / 1000).toFixed(1)} km`;
		distanceHtml = `<span class="biz-distance">${distText} away</span>`;
	}

	return `
                <div class="biz-card popup-card">
                    <div class="biz-header">
                        <span class="biz-name">${typeEmojis} ${safeName}</span>
                        <span class="biz-type">${safeType}</span>
                    </div>
                    <div class="biz-meta">
                        <span class="biz-status ${statusClass}">${escapeHtml(status.text)}</span>
                        ${distanceHtml}
                    </div>
                <p>${safeDesc}</p>
                <div class="biz-actions">
                     <a href="https://www.google.com/maps/dir/?api=1&amp;destination=${b.lat},${b.long}" target="_blank" class="btn-link">Navigate ↗</a>
                     ${b.phone ? `<a href="tel:${safePhone}" class="btn-link">Call</a>` : ""}
                     ${safeWebsite ? `<a href="${safeWebsite}" target="_blank" class="btn-link">Website ↗</a>` : ""}
                </div>
            </div>
        `;
}

function renderList(data, distances) {
	const container = document.getElementById("list-view");
	if (data.length === 0) {
		container.innerHTML =
			'<p style="text-align:center; margin-top:20px;">No results found.</p>';
		return;
	}
	let html = "";
	data.forEach((b) => {
		html += createCardHTML(b, distances ? distances.get(b) : undefined);
	});
	container.innerHTML = html;
}

function renderMap(data, distances) {
	// Clear existing cluster group
	if (markerClusterGroup) {
		map.removeLayer(markerClusterGroup);
	}
	markers = [];

	// Create new cluster group with custom icon creation
	markerClusterGroup = L.markerClusterGroup({
		maxClusterRadius: 40, // Cluster markers within 40 pixels
		spiderfyOnMaxZoom: true,
		showCoverageOnHover: false,
		zoomToBoundsOnClick: false, // We'll handle click ourselves
		iconCreateFunction: (cluster) => {
			const childMarkers = cluster.getAllChildMarkers();
			const count = childMarkers.length;

			// Get unique types in this cluster
			const types = childMarkers.map((m) => m.options.businessType);
			const uniqueTypes = [...new Set(types)];

			if (uniqueTypes.length === 1) {
				// All the same type-show stacked icon with count badge
				const iconEmoji = getIconHtml(uniqueTypes[0]);
				return L.divIcon({
					className: "stacked-icon",
					html: `${iconEmoji}<span class="stack-count">${count}</span>`,
					iconSize: [40, 40],
					iconAnchor: [20, 20],
				});
			} else {
				// Mixed types - show icons for each unique type
				const iconsHtml = uniqueTypes
					.map(
						(type) =>
							`<span class="cluster-type-icon">${getIconHtml(type)}</span>`,
					)
					.join("");

				// Calculate size based on the number of unique types
				const width = Math.min(uniqueTypes.length * 28 + 12, 120);

				// Only show count if there are more businesses than unique types
				// (i.e., some types have duplicates)
				const showCount = count > uniqueTypes.length;
				const countHtml = showCount
					? `<span class="cluster-count">${count}</span>`
					: "";

				return L.divIcon({
					className: "multi-icon-cluster",
					html: `<div class="cluster-icons">${iconsHtml}</div>${countHtml}`,
					iconSize: [width, showCount ? 44 : 30],
					iconAnchor: [width / 2, showCount ? 22 : 15],
				});
			}
		},
	});

	// Handle cluster click to show popup with all businesses
	markerClusterGroup.on("clusterclick", (e) => {
		const cluster = e.layer;
		const childMarkers = cluster.getAllChildMarkers();

		// Store original businesses that this cluster contains
		const businessesInCluster = childMarkers.map(
			(marker) => marker.options.originalBusiness,
		);

		// Build popup content with all businesses in cluster
		let popupContent = '<div class="cluster-popup-content">';
		childMarkers.forEach((marker) => {
			popupContent += marker.options.popupContent;
		});
		popupContent += "</div>";

		// Show popup at cluster location
		const popup = L.popup()
			.setLatLng(cluster.getLatLng())
			.setContent(popupContent)
			.openOn(map);

		// Track this popup
		activeClusterPopup = {
			popup: popup,
			businesses: businessesInCluster,
		};

		// Clear tracking when popup is closed
		popup.on("remove", () => {
			if (activeClusterPopup && activeClusterPopup.popup === popup) {
				activeClusterPopup = null;
			}
		});
	});

	// Add markers to cluster group
	data.forEach((b) => {
		const displayType = getDisplayType(b, currentFilter);
		const icon = L.divIcon({
			className: "custom-icon",
			html: getIconHtml(displayType),
			iconSize: [30, 30],
			iconAnchor: [15, 15],
		});

		const popupContent = createCardHTML(b, distances ? distances.get(b) : undefined);
		const marker = L.marker([b.lat, b.long], {
			icon: icon,
			businessType: displayType,
			popupContent: popupContent,
			originalBusiness: b,
		});
		marker.bindPopup(popupContent);
		markers.push(marker);
		markerClusterGroup.addLayer(marker);
	});

	// Add cluster group to map
	map.addLayer(markerClusterGroup);
}

function updateApp() {
	// Filter Data
	let filtered = filterBusinesses(businesses, currentFilter);

	// Apply "Open Now" filter
	if (openNowFilter) {
		filtered = filtered.filter((b) => getOpenStatus(b).isOpen);
	}

	// If we have user location, calculate distance and sort
	let distances = null;
	if (userLoc) {
		distances = new Map();
		filtered.forEach((b) => {
			distances.set(b, map.distance(userLoc, [b.lat, b.long]));
		});
		filtered.sort((a, b) => distances.get(a) - distances.get(b));
	}

	if (currentView === "map") renderMap(filtered, distances);
	else renderList(filtered, distances);

	// Update the active cluster popup if it exists
	if (activeClusterPopup && map.hasLayer(activeClusterPopup.popup)) {
		const filteredClusterBusinesses = filterBusinesses(
			activeClusterPopup.businesses,
			currentFilter,
		);

		if (filteredClusterBusinesses.length === 0) {
			map.closePopup(activeClusterPopup.popup);
			activeClusterPopup = null;
		} else {
			let newContent = '<div class="cluster-popup-content">';
			filteredClusterBusinesses.forEach((b) => {
				newContent += createCardHTML(b);
			});
			newContent += "</div>";
			activeClusterPopup.popup.setContent(newContent);
			activeClusterPopup.popup.update();
		}
	}
}

// --- 5. INITIALIZATION ---
window.onload = () => {
	// Build hierarchical dropdown
	buildHierarchicalDropdown();

	// Set up dropdown event handlers
	setupDropdownEvents();

	// Parse URL for Start Location
	const params = new URLSearchParams(window.location.search);
	const defaults = rawData.map_defaults || {};
	const lat = parseFloat(params.get("lat")) || defaults.lat || 37.7749;
	const lng = parseFloat(params.get("lng")) || defaults.long || -122.4194;
	const zoom = parseInt(params.get("zoom"), 10) || defaults.zoom || 15;

	// Init Map
	map = L.map("map", {
		minZoom: defaults.min_zoom || 10,
		maxBounds: defaults.max_bounds || null,
		maxBoundsViscosity: 1.0,
	}).setView([lat, lng], zoom);

	// Lightweight Tiles
	L.tileLayer(
		"https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
		{
			attribution: "&copy; OpenStreetMap &copy; CARTO",
			maxZoom: 20,
		},
	).addTo(map);

	// Initial Render
	updateApp();

	// --- EVENTS ---

	// Open Now toggle
	document.getElementById("btn-open-now").onclick = () => {
		openNowFilter = !openNowFilter;
		const btn = document.getElementById("btn-open-now");
		if (openNowFilter) {
			btn.classList.add("active");
		} else {
			btn.classList.remove("active");
		}
		updateApp();
	};

	// Toggle Map/List
	document.getElementById("btn-map").onclick = () => {
		document.getElementById("map").style.display = "block";
		document.getElementById("list-view").style.display = "none";
		document.getElementById("btn-map").classList.add("active");
		document.getElementById("btn-list").classList.remove("active");
		currentView = "map";
		updateApp();
	};

	document.getElementById("btn-list").onclick = () => {
		document.getElementById("map").style.display = "none";
		document.getElementById("list-view").style.display = "block";
		document.getElementById("btn-list").classList.add("active");
		document.getElementById("btn-map").classList.remove("active");
		currentView = "list";
		updateApp();
	};

	// Live Location
	document.getElementById("btn-loc").onclick = () => {
		if (!navigator.geolocation) return alert("Geolocation not supported");

		// Show loading state (optional)
		document.getElementById("btn-loc").textContent = "⏳";

		navigator.geolocation.getCurrentPosition(
			(pos) => {
				const { latitude, longitude } = pos.coords;
				userLoc = [latitude, longitude];

				// Add/Update User Marker
				if (userMarker) map.removeLayer(userMarker);
				userMarker = L.circleMarker(userLoc, {
					radius: 8,
					color: "blue",
					fillColor: "#2a81cb",
					fillOpacity: 1,
				}).addTo(map);

				// Center Map
				map.setView(userLoc, 16);

				document.getElementById("btn-loc").textContent = "📍 Me";

				// Update views (trigger sorting)
				updateApp();
			},
			(err) => {
				console.error(err);
				alert("Could not get location.");
				document.getElementById("btn-loc").textContent = "📍 Me";
			},
		);
	};
};
