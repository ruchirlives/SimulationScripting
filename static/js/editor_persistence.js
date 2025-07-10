// Editor input and persistence logic
export function setupEditorPersistence() {
    document.querySelectorAll(".yaml-editor").forEach((textarea) => {
        textarea.addEventListener("input", () => {
            const targetId = textarea.getAttribute("data-target");
            let stored = localStorage.getItem("file_" + targetId);
            stored = stored ? JSON.parse(stored) : { name: targetId + ".yaml", type: "text/yaml" };
            stored.content = textarea.value;
            stored.size = textarea.value.length;
            localStorage.setItem("file_" + targetId, JSON.stringify(stored));
        });
    });
}

export function restoreEditorsFromStorage() {
    const codemirrorEditors = {};
    window.codemirrorEditors = codemirrorEditors;
    window.restoreEditorsFromStorage = restoreEditorsFromStorage;
    ["yaml_file", "fcrdata_file", "supportdata_file"].forEach((id) => {
        try {
            const stored = localStorage.getItem("file_" + id);
            if (stored) {
                const data = JSON.parse(stored);
                const area = document.querySelector(`.file-upload-area[data-target="${id}"]`);
                const info = document.getElementById(id + "_info");
                const editor = document.getElementById(id + "_editor");
                if (info) {
                    info.innerHTML = `Selected: ${data.name} (${(data.size / 1024).toFixed(1)} KB) <button type="button" class="clear-file ml-2 text-red-500 hover:text-red-700" data-target="${id}">✕ Clear</button>`;
                    info.classList.remove("hidden");
                    const clearBtn = info.querySelector(".clear-file");
                    if (clearBtn) {
                        clearBtn.addEventListener("click", (e) => {
                            e.stopPropagation();
                            localStorage.removeItem("file_" + id);
                            info.classList.add("hidden");
                            if (area) area.classList.remove("border-indigo-500", "bg-indigo-50");
                            if (editor) editor.value = "";
                        });
                    }
                }
                if (editor) editor.value = data.content || "";
                // Also update the CodeMirror editor if present
                if (window.codemirrorEditors && window.codemirrorEditors[id]) {
                    window.codemirrorEditors[id].setValue(data.content || "");
                }
                if (area) area.classList.add("border-indigo-500", "bg-indigo-50");
            }
        } catch (error) {
            console.error(`Error loading ${id} from localStorage:`, error);
        }
    });
}

export function setupDownloadButtons() {
    document.querySelectorAll(".download-file").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-target");
            const storedStr = localStorage.getItem("file_" + id);
            if (storedStr) {
                const f = JSON.parse(storedStr);
                const blob = new Blob([f.content || ""], { type: "text/yaml" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = f.name || id + ".yaml";
                a.click();
                URL.revokeObjectURL(url);
            }
        });
    });
}
