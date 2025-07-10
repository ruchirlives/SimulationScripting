// Table rendering and formatting functions
export function formatCurrency(value) {
  if (typeof value === "number") {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }
  return value;
}

export function formatNumber(value) {
  if (typeof value === "number") {
    return new Intl.NumberFormat("en-GB", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  }
  return value;
}

export function renderTable(tableId, data, formatters = {}) {
  const table = document.getElementById(tableId);
  const headerRow = document.getElementById(tableId + "Header");
  const tbody = document.getElementById(tableId + "Body");
  if (!data || data.length === 0) {
    headerRow.innerHTML = '<th class="p-3 text-left font-semibold border-b-2 border-gray-300">No data available</th>';
    tbody.innerHTML = "";
    return;
  }
  let keys = [...new Set(data.flatMap(Object.keys))];
  if (tableId === "budgetTable") {
    const fixed = ["item", "description", "type"];
    const stepCols = keys.filter((k) => !fixed.includes(k)).sort((a, b) => {
      const na = parseInt((a.match(/\d+/) || [])[0]);
      const nb = parseInt((b.match(/\d+/) || [])[0]);
      return (isNaN(na) ? 0 : na) - (isNaN(nb) ? 0 : nb);
    });
    keys = [...fixed, ...stepCols];
  }
  headerRow.innerHTML = keys.map(
    (key) => `<th class="p-3 text-left font-semibold border-b-2 border-gray-300">${key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ")}</th>`
  ).join("");
  tbody.innerHTML = data.map((row) => {
    return (
      '<tr class="even:bg-gray-50 hover:bg-blue-50">' +
      keys.map((key) => {
        let value = row[key] || "";
        let cellClass = "p-3 border-b border-gray-100 align-top";
        let originalValue = value;
        if (formatters[key]) {
          value = formatters[key](value);
          cellClass += " text-right font-mono font-medium";
          if (key.includes("budget") || key.includes("amount") || key.includes("cost")) {
            cellClass += " text-green-600";
            if (typeof originalValue === "number" && originalValue < 0) {
              cellClass += " text-red-600";
            }
          }
        }
        return `<td class="${cellClass}">${value}</td>`;
      }).join("") +
      "</tr>"
    );
  }).join("");
}

export function createPivotTable(budgetData) {
  if (!budgetData || budgetData.length === 0) return [];
  const grouped = {};
  budgetData.forEach((row) => {
    const item = row.item || "Unknown";
    if (!grouped[item]) {
      grouped[item] = {
        item: item,
        description: row.description || "",
        type: row.type || "",
      };
    }
    const step = `Step ${row.step || 0}`;
    grouped[item][step] = (grouped[item][step] || 0) + (row.budget || 0);
  });
  return Object.values(grouped);
}
