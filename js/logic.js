/**
 * Logic for Sunset Dunes Business Map
 *
 * categoryHierarchy is injected as a global from data.toml at build time.
 * In tests it is provided via require() or global assignment.
 */

// Get all subcategory types for a broad category
function getSubcategoryTypes(broadCategory) {
	if (categoryHierarchy[broadCategory]) {
		return Object.keys(categoryHierarchy[broadCategory].subcategories);
	}
	return [];
}

// Check if a type belongs to a broad category
function typeInBroadCategory(type, broadCategory) {
	const subcats = getSubcategoryTypes(broadCategory);
	return subcats.includes(type);
}

function getOpenStatus(b, now = new Date()) {
	const days = [
		"sunday",
		"monday",
		"tuesday",
		"wednesday",
		"thursday",
		"friday",
		"saturday",
	];
	const dayName = days[now.getDay()];
	const yyyy = now.getFullYear();
	const mm = String(now.getMonth() + 1).padStart(2, "0");
	const dd = String(now.getDate()).padStart(2, "0");
	const dateString = `${yyyy}-${mm}-${dd}`;

	// Check Holidays first
	let hoursStr = null;
	if (b.holiday_hours?.[dateString]) {
		hoursStr = b.holiday_hours[dateString];
	} else if (b.hours) {
		hoursStr = b.hours[dayName] || b.hours.default;
	}

	if (!hoursStr || hoursStr === "Closed")
		return { isOpen: false, text: "Closed today" };

	// Parse "07:00-16:00"
	const [start, end] = hoursStr.split("-");
	const [sh, sm] = start.split(":").map(Number);
	const [eh, em] = end.split(":").map(Number);

	const nowMinutes = now.getHours() * 60 + now.getMinutes();
	const startMinutes = sh * 60 + sm;
	const endMinutes = eh * 60 + em;

	const isOpen = nowMinutes >= startMinutes && nowMinutes < endMinutes;
	let text;
	if (isOpen) {
		text = `Open until ${end}`;
	} else if (nowMinutes < startMinutes) {
		text = `Closed (Opens ${start})`;
	} else {
		text = "Closed for the day";
	}
	return { isOpen, text };
}

function getIconHtml(type) {
	for (const cat of Object.values(categoryHierarchy)) {
		if (cat.subcategories[type]) return cat.subcategories[type].emoji;
	}
	return "📍";
}

function getDisplayLabel(type) {
	for (const cat of Object.values(categoryHierarchy)) {
		if (cat.subcategories[type]) return cat.subcategories[type].label;
	}
	return type;
}

function getDisplayType(b, filterType) {
	if (filterType && filterType !== "all") {
		const types = Array.isArray(b.type) ? b.type : [b.type];

		// If filterType is a specific subcategory, return it if the business has it
		if (types.includes(filterType)) return filterType;

		// If filterType is a broad category, find the matching subcategory
		if (categoryHierarchy[filterType]) {
			const subcatTypes = getSubcategoryTypes(filterType);
			const matchingType = types.find((t) => subcatTypes.includes(t));
			if (matchingType) return matchingType;
		}
	}
	return Array.isArray(b.type) ? b.type[0] : b.type;
}

function filterBusinesses(businesses, filterType) {
	if (filterType === "all") return businesses;

	// Check if filterType is a broad category
	if (categoryHierarchy[filterType]) {
		const subcatTypes = getSubcategoryTypes(filterType);
		return businesses.filter((b) => {
			const types = Array.isArray(b.type) ? b.type : [b.type];
			return types.some((t) => subcatTypes.includes(t));
		});
	}

	// Otherwise filter by specific subcategory type
	return businesses.filter((b) => {
		if (Array.isArray(b.type)) {
			return b.type.includes(filterType);
		}
		return b.type === filterType;
	});
}

// Export for Node/Tests
if (typeof module !== "undefined" && module.exports) {
	module.exports = {
		getOpenStatus,
		getIconHtml,
		getDisplayLabel,
		filterBusinesses,
		getDisplayType,
		categoryHierarchy,
		getSubcategoryTypes,
		typeInBroadCategory,
	};
}
