// Tab switching logic
export function showTab(tabId) {
  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.add("hidden");
    content.classList.remove("block");
  });
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active", "border-b-indigo-500", "text-indigo-500", "bg-blue-50");
    btn.classList.add("border-b-transparent", "text-gray-600");
  });
  document.getElementById(tabId).classList.remove("hidden");
  document.getElementById(tabId).classList.add("block");
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    if (btn.getAttribute("onclick").includes(tabId)) {
      btn.classList.add("active", "border-b-indigo-500", "text-indigo-500", "bg-blue-50");
      btn.classList.remove("border-b-transparent", "text-gray-600");
    }
  });
}
