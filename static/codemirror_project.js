window.addEventListener("DOMContentLoaded", () => {
  // Select all YAML editor textareas
  document.querySelectorAll("textarea.yaml-editor").forEach((textarea) => {
    const cmDiv = document.createElement("div");
    cmDiv.style = "min-height: 250px;";
    textarea.parentNode.insertBefore(cmDiv, textarea);
    textarea.style.display = "none";

    const editor = CodeMirror(cmDiv, {
      value: textarea.value,
      mode: "yaml",
      lineNumbers: true,
      theme: "monokai", // or "default"
      indentUnit: 2,
    });

    editor.on("change", () => {
      textarea.value = editor.getValue();
    });
  });
});
