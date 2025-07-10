import { formatCurrency, formatNumber, renderTable, createPivotTable } from './table_rendering.js';
import { showTab } from './tab_handling.js';

// Form submission and response handling
export function setupFormSubmission() {
  document.getElementById("simulationForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData();
    let hasRequiredFiles = false;
    const submitBtn = document.getElementById("submitBtn");
    const responseArea = document.getElementById("responseArea");
    const tabContainer = document.getElementById("tabContainer");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const responseContent = document.getElementById("responseContent");
    try {
      function appendEditorFile(id, required = false) {
        const editor = document.getElementById(id + "_editor");
        const content = editor?.value?.trim();
        if (content) {
          const storedMeta = localStorage.getItem("file_" + id);
          const meta = storedMeta ? JSON.parse(storedMeta) : { name: id + ".yaml", type: "text/yaml" };
          formData.append(id, new File([content], meta.name, { type: meta.type || "text/yaml" }));
          if (id === "yaml_file") hasRequiredFiles = true;
        } else if (required) {
          alert("Please enter YAML configuration in the editor.");
          throw new Error(`Missing YAML content in ${id}_editor`);
        }
      }
      appendEditorFile("yaml_file", true);
      appendEditorFile("fcrdata_file", false);
      appendEditorFile("supportdata_file", false);
      formData.append("steps", document.getElementById("steps").value);
    } catch (error) {
      console.error("Error preparing form data:", error);
      submitBtn.disabled = false;
      submitBtn.textContent = "🚀 Run Simulation";
      return;
    }
    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Running...";
    responseArea.classList.remove("hidden");
    responseArea.classList.add("block");
    tabContainer.classList.add("hidden");
    loadingIndicator.classList.remove("hidden");
    try {
      const response = await fetch("/simulate", {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      if (response.ok) {
        tabContainer.classList.remove("hidden");
        const budgetFormatters = { budget: formatCurrency, step: formatNumber };
        const projectFormatters = { budget: formatCurrency, cost: formatCurrency, income: formatCurrency, term: formatNumber };
        const transactionFormatters = { amount: formatCurrency, balance: formatCurrency, date: formatNumber };
        let budgetTableData;
        if (result.budget_pivot && result.budget_pivot.length > 0) {
          budgetTableData = result.budget_pivot;
          const pivotFormatters = {};
          if (budgetTableData.length > 0) {
            Object.keys(budgetTableData[0]).forEach((key) => {
              if (key.match(/^\d+$/) || key.includes("Step")) {
                pivotFormatters[key] = formatCurrency;
              }
            });
          }
          renderTable("budgetTable", budgetTableData, pivotFormatters);
        } else {
          budgetTableData = createPivotTable(result.budget || []);
          const stepColumns = {};
          (result.budget || []).forEach((row) => {
            const step = `Step ${row.step || 0}`;
            stepColumns[step] = formatCurrency;
          });
          const pivotFormatters = { ...stepColumns };
          renderTable("budgetTable", budgetTableData, pivotFormatters);
        }
        renderTable("projectsTable", result.projects || [], projectFormatters);
        renderTable("transactionsTable", result.transactions || [], transactionFormatters);
        responseContent.textContent = JSON.stringify(result, null, 2);
        responseContent.classList.remove("text-red-500");
        responseContent.classList.add("text-green-600");
      } else {
        tabContainer.classList.remove("hidden");
        showTab("raw-json");
        responseContent.textContent = JSON.stringify(result, null, 2);
        responseContent.classList.remove("text-green-600");
        responseContent.classList.add("text-red-500");
      }
    } catch (error) {
      tabContainer.classList.remove("hidden");
      showTab("raw-json");
      responseContent.textContent = `Error: ${error.message}`;
      responseContent.classList.remove("text-green-600");
      responseContent.classList.add("text-red-500");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "🚀 Run Simulation";
      loadingIndicator.classList.add("hidden");
    }
  });
}
