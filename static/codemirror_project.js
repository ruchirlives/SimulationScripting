// Include these <script> and <link> tags in your base.html or layout:
// <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/codemirror.min.css" />
// <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/theme/monokai.min.css" />
// <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/addon/hint/show-hint.min.css" />
// <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/codemirror.min.js"></script>
// <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/mode/yaml/yaml.min.js"></script>
// <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/addon/hint/show-hint.min.js"></script>
// <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/addon/hint/anyword-hint.min.js"></script>

window.addEventListener("DOMContentLoaded", () => {
    const contextualHints = {
        projects: ["term", "name", "directcosts", "supports", "portfolio", "startstep"],
        directcosts: ["item", "cost", "frequency", "description"],
        frequency: ["monthly", "annual", "one-off"],
        staffing: ["name", "role", "salary", "fte", "linemanagerrate", "employerpensionrate", "description"],
        policies: ["policy", "description", "frequency", "amount", "fund", "step"],
        policy: ["FullCostRecovery", "Grant", "Finance", "CarbonFinancing"],
        FullCostRecovery: ["fcrdata", "linemanagerrate", "fte", "step"],
        Grant: ["amount", "fund", "step"],
        Finance: ["term", "capital", "rate"],
        CarbonFinancing: ["term", "capital", "rate", "investment", "tree_planting_cost_per_unit", "carbon_credit_per_unit"]
    };

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
                return {
                    list: contextualHints[key].map((v) => {
                        // If value should be quoted (e.g. frequency options), add quotes
                        const needsQuotes = key === "frequency";
                        return {
                            text: needsQuotes ? `"${v}"` : v,
                            displayText: v,
                        };
                    }),
                    from: CodeMirror.Pos(cursor.line, line.indexOf(valuePart)),
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
        const cmDiv = document.createElement("div");
        cmDiv.style = "min-height: 250px;";
        textarea.parentNode.insertBefore(cmDiv, textarea);
        textarea.style.display = "none";

        const editor = CodeMirror(cmDiv, {
            value: textarea.value,
            mode: "yaml",
            theme: "monokai",
            lineNumbers: true,
            indentUnit: 2,
            extraKeys: {
                "Ctrl-Space": "autocomplete"
            },
            hintOptions: {
                hint: yamlContextHint,
                completeSingle: false
            }
        });

        // Set the editor
        codemirrorEditors[textarea.getAttribute("data-target")] = editor;

        // Live sync to textarea
        editor.on("change", () => {
            textarea.value = editor.getValue();
        });

        // Trigger autocomplete on typing
        editor.on("inputRead", (cm, change) => {
            if (change.text[0].match(/[\w\-]/)) {
                cm.showHint({ hint: yamlContextHint, completeSingle: false });
            }
        });
    });
});
