import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfyui-text-templates.ShowText",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ShowText") {
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                if (message?.text) {
                    const text = message.text.join("");

                    if (!this.widgets) {
                        this.widgets = [];
                    }

                    // Find or create the text widget
                    let widget = this.widgets.find(w => w.name === "display_text");
                    if (!widget) {
                        widget = this.addWidget("text", "display_text", "", () => {}, {
                            multiline: true,
                            readonly: true,
                        });
                        widget.inputEl.readOnly = true;
                        widget.inputEl.style.opacity = 0.8;
                    }

                    widget.value = text;
                    this.setSize(this.computeSize());
                }
            };
        }
    },
});
