window.addEventListener("DOMContentLoaded", () => {
    const contextualHints = {
        projects: ["time", "term", "name", "directcosts", "supports", "portfolio", "startstep", "staffing", "policies", "description"],
        directcosts: ["item", "cost", "frequency", "description"],
        supports: ["item", "step", "description", "frequency", "units"],

        staffing: ["name", "role", "salary", "fte", "linemanagerrate", "employerpensionrate", "description"],
        policies: ["policy", "description", "frequency", "amount", "fund", "step"],
        policy: ["FullCostRecovery", "Grant", "Finance", "CarbonFinancing"],
        Grant: ["amount", "fund", "step"],
        Finance: ["term", "capital", "rate"],
        CarbonFinancing: ["term", "capital", "rate", "investment", "tree_planting_cost_per_unit", "carbon_credit_per_unit"],

        item: [],
        frequency: ["monthly", "annual", "oneoff"],
        dayrate: [],
        daysperfte: [],
        units: [],



    };
    function highlightKeywords(editor, keywords) {
        const doc = editor.getDoc();
        editor.getAllMarks().forEach(mark => mark.clear());

        keywords.forEach(word => {
            const cursor = doc.getSearchCursor(new RegExp(`\\b${word}\\b`, "g"));
            while (cursor.findNext()) {
                editor.markText(cursor.from(), cursor.to(), {
                    className: "cm-keyword-highlight"
                });
            }
        });
    }

    const allYamlKeywords = Array.from(
        new Set(Object.keys(contextualHints).concat(...Object.values(contextualHints)))
    );

    function yamlContextHint(cm) {
        const cursor = cm.getCursor();
        const token = cm.getTokenAt(cursor);
        const line = cm.getLine(cursor.line);
        const indent = line.search(/\S|$/);
        const trimmed = line.trim();
        let currentWord = token.string.trim();
        if (currentWord === "-" || currentWord === "") {
            currentWord = "";
        }


        let contextKey = null;
        let listPrefix = "";

        // Check if we're starting a list item
        if (trimmed.startsWith("-")) {
            listPrefix = "- ";
        }

        // Case 1: value completion
        const keyValueMatch = trimmed.match(/^[- ]*\s*(\w+):\s*(\S*)?$/);
        if (keyValueMatch) {
            const key = keyValueMatch[1];
            const valuePart = keyValueMatch[2] || "";
            if (contextualHints[key]) {
                const suggestions = contextualHints[key].map((v) => ({
                    text: ` ` + v,
                    displayText: v
                }));

                // If valuePart is empty, insert at end of line (after colon)
                const colonIndex = line.indexOf(":");
                const insertPos = valuePart
                    ? CodeMirror.Pos(cursor.line, line.indexOf(valuePart))
                    : CodeMirror.Pos(cursor.line, colonIndex + 1);

                return {
                    list: suggestions,
                    from: insertPos,
                    to: CodeMirror.Pos(cursor.line, cursor.ch),
                };
            }
        }

        // Case 2: determine context from parent keys
        for (let i = cursor.line - 1; i >= 0; i--) {
            const prev = cm.getLine(i);
            const prevIndent = prev.search(/\S|$/);
            if (prevIndent < indent && prev.match(/:/)) {
                const [key] = prev.trim().split(":");
                if (contextualHints[key]) {
                    contextKey = key;
                    break;
                }
            }
        }

        const rawSuggestions = contextualHints[contextKey] || Object.keys(contextualHints);

        // Build suggestion list with proper prefix
        const list = rawSuggestions.map(key => ({
            text: `${listPrefix}${key}: `,
            displayText: key
        }));

        return {
            list: currentWord
                ? list.filter(item => item.displayText.startsWith(currentWord))
                : list, // show all if nothing typed yet
            from: CodeMirror.Pos(cursor.line, line.search(/\S|$/)),
            to: CodeMirror.Pos(cursor.line, token.end)
        };

    }

    // Attach CodeMirror to each textarea.yaml-editor
    document.querySelectorAll("textarea.yaml-editor").forEach((textarea) => {
        // Ensure codemirrorEditors is defined globally
        if (typeof window.codemirrorEditors === 'undefined') {
            window.codemirrorEditors = {};
        }
        const codemirrorEditors = window.codemirrorEditors;
        const cmDiv = document.createElement("div");
        cmDiv.style = "min-height: 250px;";
        textarea.parentNode.insertBefore(cmDiv, textarea);
        textarea.style.display = "none";

        const targetId = textarea.getAttribute("data-target");

        // Try to get restored content from localStorage
        let initialContent = "";
        try {
            const stored = localStorage.getItem("file_" + targetId);
            if (stored) {
                const parsed = JSON.parse(stored);
                if (parsed.content) {
                    initialContent = parsed.content;
                }
            }
        } catch (e) {
            console.warn(`Could not restore ${targetId} from localStorage`, e);
        }


        const editor = CodeMirror(cmDiv, {
            value: initialContent,
            mode: "yaml",
            theme: "monokai",
            lineNumbers: true,
            indentUnit: 2,
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Tab": function (cm) {
                    cm.replaceSelection("  ", "end"); // insert 2 spaces
                },
                "Shift-Tab": "indentLess"
            },
            hintOptions: {
                hint: yamlContextHint,
                completeSingle: false
            }
        });

        // Trigger one-time highlight after CM renders fully
        let initialHighlightDone = false;
        editor.on("changes", () => {
            if (!initialHighlightDone) {
                highlightKeywords(editor, allYamlKeywords);
                initialHighlightDone = true;
            }
        });


        // Set the editor
        codemirrorEditors[textarea.getAttribute("data-target")] = editor;
        // Apply any file-loaded YAML content to the editor (if waiting)
        if (window.pendingCodemirrorUpdates && window.pendingCodemirrorUpdates[targetId]) {
            const pending = window.pendingCodemirrorUpdates[targetId];
            editor.setValue(pending);

            setTimeout(() => {
                highlightKeywords(editor, allYamlKeywords);
            }, 20); // allow layout to settle

            delete window.pendingCodemirrorUpdates[targetId];
        } else {
            // If no pending override, highlight what was loaded via initialContent
            setTimeout(() => {
                highlightKeywords(editor, allYamlKeywords);
            }, 20);
        }



        // Live sync to textarea
        editor.on("change", () => {
            const content = editor.getValue();
            textarea.value = content;

            let stored = localStorage.getItem("file_" + targetId);
            stored = stored ? JSON.parse(stored) : { name: targetId + ".yaml", type: "text/yaml" };
            stored.content = content;
            stored.size = content.length;

            localStorage.setItem("file_" + targetId, JSON.stringify(stored));

            // Highlight keywords
            setTimeout(() => {
                highlightKeywords(editor, allYamlKeywords);
            }, 10);
        });
        // Trigger autocomplete on typing
        editor.on("inputRead", (cm, change) => {
            if (change.text[0].match(/[\w\-]/)) {
                cm.showHint({ hint: yamlContextHint, completeSingle: false });
            }
        });
    });

});
