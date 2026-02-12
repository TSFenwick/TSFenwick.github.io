/**
 * @jest-environment jsdom
 */

// Define categoryHierarchy globally before loading logic.js (mirrors build-time injection)
global.categoryHierarchy = {
	food: {
		emoji: "🍴",
		label: "Food",
		subcategories: {
			bakery: { emoji: "🥖", label: "Bakery" },
			restaurant: { emoji: "🍽", label: "Restaurant" },
			cafe: { emoji: "☕", label: "Café" },
		},
	},
	drink: {
		emoji: "🍹",
		label: "Drink",
		subcategories: {
			bar: { emoji: "🍺", label: "Bar" },
			cafe: { emoji: "☕", label: "Café" },
		},
	},
	shopping: {
		emoji: "🛒",
		label: "Shopping",
		subcategories: {
			bookstore: { emoji: "📚", label: "Bookstore" },
			bikeshop: { emoji: "🚲", label: "Bike Shop" },
			store: { emoji: "🛍️", label: "Store" },
		},
	},
};

const {
	getOpenStatus,
	getIconHtml,
	getDisplayLabel,
	filterBusinesses,
	getDisplayType,
	getSubcategoryTypes,
	typeInBroadCategory,
} = require("../js/logic.js");
global.getOpenStatus = getOpenStatus;
global.getIconHtml = getIconHtml;
global.getDisplayLabel = getDisplayLabel;
global.filterBusinesses = filterBusinesses;
global.getDisplayType = getDisplayType;
global.getSubcategoryTypes = getSubcategoryTypes;
global.typeInBroadCategory = typeInBroadCategory;

// escapeHtml utility from main.js — defined here so the eval'd code can access it
function escapeHtml(str) {
	if (!str) return "";
	return str
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}
global.escapeHtml = escapeHtml;

// We need to extract functions from main.js for testing.
// Since main.js uses globals and window.onload, we'll eval it in a controlled way.
const fs = require("node:fs");
const path = require("node:path");

// Helper to set up the minimal DOM structure the app expects
function setupDOM() {
	document.body.innerHTML = `
		<header>
			<div id="filter-dropdown" class="dropdown">
				<div class="dropdown-selected"></div>
				<div class="dropdown-options"></div>
			</div>
			<button id="btn-open-now">⏰ Open Now</button>
			<button id="btn-map" class="active">Map</button>
			<button id="btn-list">List</button>
			<button id="btn-loc">📍 Me</button>
		</header>
		<div id="map"></div>
		<div id="list-view"></div>
	`;
}

// Load main.js source to extract functions via eval in a controlled scope
function loadMainFunctions() {
	const src = fs.readFileSync(
		path.join(__dirname, "..", "js", "main.js"),
		"utf-8",
	);
	// Extract individual functions by wrapping in a module-like scope
	// We strip the window.onload block and state declarations, then return the functions
	const wrapped = `
		(function() {
			let map, userMarker;
			let currentView = "map";
			let currentFilter = "all";
			let userLoc = null;
			let markers = [];
			let markerClusterGroup = null;
			const expandedCategories = {};
			let activeClusterPopup = null;
			const businesses = [];
 		${src.replace(/^\/\/ --- 1\. UTILITIES ---[\s\S]*?\/\/ --- 3\./, "// --- 3.").replace(/\/\/ --- 5\. INITIALIZATION ---[\s\S]*$/, "")}
			return { buildHierarchicalDropdown, setupDropdownEvents, createCardHTML, renderList, updateApp };
		})();
	`;
	return eval(wrapped);
}

describe("UI Tests", () => {
	let mainFns;

	beforeEach(() => {
		setupDOM();
		mainFns = loadMainFunctions();
	});

	describe("createCardHTML", () => {
		test("renders business name and description", () => {
			const biz = {
				name: "Test Cafe",
				type: "cafe",
				description: "A cozy cafe",
				lat: 37.75,
				long: -122.5,
				phone: "415-555-1234",
				hours: { default: "09:00-17:00" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("Test Cafe");
			expect(html).toContain("A cozy cafe");
		});

		test("renders phone link when phone is provided", () => {
			const biz = {
				name: "Biz",
				type: "bar",
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				phone: "415-555-0000",
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain('href="tel:415-555-0000"');
			expect(html).toContain("Call");
		});

		test("omits phone link when phone is missing", () => {
			const biz = {
				name: "Biz",
				type: "store",
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).not.toContain("tel:");
			expect(html).not.toContain("Call</a>");
		});

		test("renders navigation link with lat/long", () => {
			const biz = {
				name: "Biz",
				type: "cafe",
				description: "Desc",
				lat: 37.123,
				long: -122.456,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("destination=37.123,-122.456");
			expect(html).toContain("Navigate");
		});

		test("shows open status for open business", () => {
			// Mock a business that is open now
			const now = new Date();
			const dayNames = [
				"sunday",
				"monday",
				"tuesday",
				"wednesday",
				"thursday",
				"friday",
				"saturday",
			];
			const hours = {};
			hours[dayNames[now.getDay()]] = "00:00-23:59";
			const biz = {
				name: "Open Biz",
				type: "cafe",
				description: "Always open",
				lat: 37.75,
				long: -122.5,
				hours: hours,
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("open");
			expect(html).toContain("Open until");
		});

		test("shows closed status for closed business", () => {
			const biz = {
				name: "Closed Biz",
				type: "cafe",
				description: "Always closed",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("closed");
			expect(html).toContain("Closed today");
		});

		test("renders joined type for multi-type business", () => {
			const biz = {
				name: "Multi",
				type: ["cafe", "bar"],
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("Caf\u00e9 &amp; Bar");
		});

		test("renders website link when website is provided", () => {
			const biz = {
				name: "Biz",
				type: "cafe",
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
				website: "https://example.com",
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain('href="https://example.com"');
			expect(html).toContain("Website");
		});

		test("renders distance when provided", () => {
			const biz = {
				name: "Biz",
				type: "cafe",
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz, 450);
			expect(html).toContain("450 m away");
		});

		test("renders distance in km for large distances", () => {
			const biz = {
				name: "Biz",
				type: "cafe",
				description: "Desc",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz, 2500);
			expect(html).toContain("2.5 km away");
		});

		test("shows type emojis on cards", () => {
			const biz = {
				name: "Test Cafe",
				type: "cafe",
				description: "A cafe",
				lat: 37.75,
				long: -122.5,
				hours: { default: "Closed" },
			};
			const html = mainFns.createCardHTML(biz);
			expect(html).toContain("☕");
		});
	});

	describe("renderList", () => {
		test("renders business cards into list-view container", () => {
			const businesses = [
				{
					name: "Biz A",
					type: "cafe",
					description: "Desc A",
					lat: 37.75,
					long: -122.5,
					hours: { default: "Closed" },
				},
				{
					name: "Biz B",
					type: "bar",
					description: "Desc B",
					lat: 37.75,
					long: -122.5,
					hours: { default: "Closed" },
				},
			];
			mainFns.renderList(businesses);
			const container = document.getElementById("list-view");
			expect(container.innerHTML).toContain("Biz A");
			expect(container.innerHTML).toContain("Biz B");
		});

		test("shows no results message for empty list", () => {
			mainFns.renderList([]);
			const container = document.getElementById("list-view");
			expect(container.innerHTML).toContain("No results found");
		});

		test("clears previous content before rendering", () => {
			const container = document.getElementById("list-view");
			container.innerHTML = "<p>Old content</p>";
			mainFns.renderList([
				{
					name: "New",
					type: "cafe",
					description: "D",
					lat: 0,
					long: 0,
					hours: { default: "Closed" },
				},
			]);
			expect(container.innerHTML).not.toContain("Old content");
			expect(container.innerHTML).toContain("New");
		});
	});

	describe("buildHierarchicalDropdown", () => {
		test("populates dropdown with All Places option", () => {
			mainFns.buildHierarchicalDropdown();
			const options = document.querySelector(".dropdown-options");
			expect(options.innerHTML).toContain("All Places");
		});

		test("populates dropdown with category headers", () => {
			mainFns.buildHierarchicalDropdown();
			const options = document.querySelector(".dropdown-options");
			expect(options.innerHTML).toContain("Food");
			expect(options.innerHTML).toContain("Drink");
			expect(options.innerHTML).toContain("Shopping");
		});

		test("populates dropdown with subcategories", () => {
			mainFns.buildHierarchicalDropdown();
			const options = document.querySelector(".dropdown-options");
			expect(options.innerHTML).toContain("Bakery");
			expect(options.innerHTML).toContain("Restaurant");
			expect(options.innerHTML).toContain("Café");
			expect(options.innerHTML).toContain("Bar");
			expect(options.innerHTML).toContain("Bookstore");
		});

		test("sets initial selected display to All Places", () => {
			mainFns.buildHierarchicalDropdown();
			const selected = document.querySelector(".dropdown-selected");
			expect(selected.textContent).toContain("All Places");
			expect(selected.innerHTML).toContain("▼");
		});
	});

	describe("setupDropdownEvents", () => {
		beforeEach(() => {
			mainFns.buildHierarchicalDropdown();
			mainFns.setupDropdownEvents();
		});

		test("toggles dropdown open on click", () => {
			const container = document.getElementById("filter-dropdown");
			const selected = container.querySelector(".dropdown-selected");

			expect(container.classList.contains("open")).toBe(false);
			selected.click();
			expect(container.classList.contains("open")).toBe(true);
			selected.click();
			expect(container.classList.contains("open")).toBe(false);
		});

		test("closes dropdown when clicking outside", () => {
			const container = document.getElementById("filter-dropdown");
			const selected = container.querySelector(".dropdown-selected");

			selected.click();
			expect(container.classList.contains("open")).toBe(true);

			// Click outside
			document.body.click();
			expect(container.classList.contains("open")).toBe(false);
		});

		test("expands subcategory list on toggle click", () => {
			const container = document.getElementById("filter-dropdown");
			const selected = container.querySelector(".dropdown-selected");
			selected.click();

			const toggle = document.querySelector(
				'.expand-toggle[data-category="food"]',
			);
			const subcatList = document.querySelector(
				'.subcategory-list[data-category="food"]',
			);

			expect(subcatList.classList.contains("expanded")).toBe(false);
			toggle.click();
			expect(subcatList.classList.contains("expanded")).toBe(true);
			expect(toggle.textContent).toBe("▼");

			// Collapse
			toggle.click();
			expect(subcatList.classList.contains("expanded")).toBe(false);
			expect(toggle.textContent).toBe("▶");
		});
	});
});
