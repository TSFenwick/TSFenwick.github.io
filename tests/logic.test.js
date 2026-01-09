const {
	getOpenStatus,
	getIconHtml,
	filterBusinesses,
} = require("../js/logic.js");

describe("Business Logic", () => {
	describe("getIconHtml", () => {
		test("returns correct icon for known types", () => {
			expect(getIconHtml("cafe")).toBe("☕");
			expect(getIconHtml("bar")).toBe("🍺");
		});

		test("returns default icon for unknown type", () => {
			expect(getIconHtml("unknown")).toBe("📍");
		});
	});

	describe("filterBusinesses", () => {
		const businesses = [
			{ id: 1, type: "cafe" },
			{ id: 2, type: ["bar", "cafe"] },
			{ id: 3, type: "store" },
		];

		test("returns all businesses when filter is all", () => {
			expect(filterBusinesses(businesses, "all")).toHaveLength(3);
		});

		test("filters by exact type", () => {
			const result = filterBusinesses(businesses, "store");
			expect(result).toHaveLength(1);
			expect(result[0].id).toBe(3);
		});

		test("filters by type in array", () => {
			const cafes = filterBusinesses(businesses, "cafe");
			expect(cafes).toHaveLength(2); // id 1 and 2
		});
	});

	describe("getOpenStatus", () => {
		const business = {
			hours: {
				monday: "09:00-17:00",
				tuesday: "09:00-17:00",
				default: "10:00-16:00",
			},
			holiday_hours: {
				"2025-12-25": "Closed",
			},
		};

		test("is open during business hours on Monday", () => {
			// Jan 6 2025 is a Monday
			const date = new Date("2025-01-06T10:00:00");
			const status = getOpenStatus(business, date);
			expect(status.isOpen).toBe(true);
			expect(status.text).toContain("Open until 17:00");
		});

		test("is closed before opening time", () => {
			const date = new Date("2025-01-06T08:00:00");
			const status = getOpenStatus(business, date);
			expect(status.isOpen).toBe(false);
			expect(status.text).toContain("Closed (Opens 09:00)");
		});

		test("is closed after closing time", () => {
			const date = new Date("2025-01-06T18:00:00");
			const status = getOpenStatus(business, date);
			expect(status.isOpen).toBe(false);
			expect(status.text).toContain("Closed");
		});

		test("uses default hours when specific day not defined (Wednesday)", () => {
			// Jan 8 2025 is Wednesday.
			const date = new Date("2025-01-08T11:00:00"); // Within 10-16
			const status = getOpenStatus(business, date);
			expect(status.isOpen).toBe(true);
			expect(status.text).toContain("Open until 16:00");
		});

		test("respects holiday hours", () => {
			// 2025-12-25 is Thursday.
			const date = new Date("2025-12-25T12:00:00");
			const status = getOpenStatus(business, date);
			expect(status.isOpen).toBe(false);
			expect(status.text).toBe("Closed today");
		});

		test("handles closed status in regular hours", () => {
			const b = { hours: { default: "Closed" } };
			const date = new Date("2025-01-06T12:00:00");
			const status = getOpenStatus(b, date);
			expect(status.isOpen).toBe(false);
			expect(status.text).toBe("Closed today");
		});
	});
});
