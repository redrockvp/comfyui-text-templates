import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "comfyui-text-templates.ShowText",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ShowText") {
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                if (message?.text) {
                    const text = message.text.join("");

                    // Find or create the text widget
                    let widget = this.widgets?.find(w => w.name === "display_text");
                    if (!widget) {
                        widget = ComfyWidgets["STRING"](this, "display_text", ["STRING", { multiline: true }], app).widget;
                        widget.inputEl.readOnly = true;
                        widget.inputEl.style.opacity = 0.9;
                        widget.inputEl.style.cursor = "default";
                    }

                    widget.value = text;

                    // Resize node to fit content
                    const minHeight = 150;
                    const lineCount = text.split("\n").length;
                    const textHeight = Math.max(minHeight, Math.min(400, lineCount * 20 + 50));
                    this.setSize([this.size[0], textHeight]);
                }
            };
        }
    },
});
