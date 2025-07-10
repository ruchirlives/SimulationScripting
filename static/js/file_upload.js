// File upload handling and clear functionality
export function setupFileUpload() {
    document.querySelectorAll(".file-upload-area").forEach((area) => {
        const input = area.querySelector('input[type="file"]');
        const info = area.querySelector(".file-info");

        area.addEventListener("click", () => input.click());

        // Drag and drop
        area.addEventListener("dragover", (e) => {
            e.preventDefault();
            area.classList.add("border-indigo-500", "bg-indigo-50");
        });

        area.addEventListener("dragleave", () => {
            area.classList.remove("border-indigo-500", "bg-indigo-50");
        });

        area.addEventListener("drop", (e) => {
            e.preventDefault();
            area.classList.remove("border-indigo-500", "bg-indigo-50");

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                updateFileInfo(input, info);
            }
        });

        input.addEventListener("change", () => {
            updateFileInfo(input, info);
        });
    });

    document.querySelectorAll(".clear-file").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const targetId = btn.getAttribute("data-target");
            const area = document.querySelector(`.file-upload-area[data-target="${targetId}"]`);
            const input = document.getElementById(targetId);
            const info = document.getElementById(targetId + "_info");
            input.value = "";
            localStorage.removeItem("file_" + targetId);
            info.classList.add("hidden");
            area.classList.remove("border-indigo-500", "bg-indigo-50");
            const editor = document.getElementById(targetId + "_editor");
            if (editor) {
                editor.value = "";
            }
        });
    });
}

export function updateFileInfo(input, info) {
    if (input.files.length > 0) {
        const file = input.files[0];
        info.innerHTML = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB) <button type="button" class="clear-file ml-2 text-red-500 hover:text-red-700" data-target="${input.id}">✕ Clear</button>`;
        info.classList.remove("hidden");
        const clearBtn = info.querySelector(".clear-file");
        if (clearBtn) {
            clearBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                input.value = "";
                localStorage.removeItem("file_" + input.id);
                info.classList.add("hidden");
                const area = document.querySelector(`.file-upload-area[data-target="${input.id}"]`);
                if (area) {
                    area.classList.remove("border-indigo-500", "bg-indigo-50");
                }
            });
        }
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const content = event.target.result;
                const payload = { name: file.name, size: file.size, type: file.type, content };
                localStorage.setItem("file_" + input.id, JSON.stringify(payload));

                const textarea = document.getElementById(input.id + "_editor");
                if (textarea) {
                    textarea.value = content;
                }

                if (window.codemirrorEditors && window.codemirrorEditors[input.id]) {
                    window.codemirrorEditors[input.id].setValue(content); // ✅ force update here
                }
            } catch (error) {
                console.error(`Error saving file ${file.name} to localStorage:`, error);
            }
        };

        reader.readAsText(file);
    } else {
        info.classList.add("hidden");
    }
}
