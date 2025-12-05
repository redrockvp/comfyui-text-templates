import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
import { api } from "../../scripts/api.js";

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

// ImageTextIterator extension - image preview with text editing for batch iteration
app.registerExtension({
    name: "comfyui-text-templates.ImageTextIterator",
    async setup() {
        // Listen for image_text_iterator_update messages
        api.addEventListener("image_text_iterator_update", (event) => {
            const data = event.detail;
            if (!data) return;

            const nodes = app.graph._nodes.filter(n => n.type === "ImageTextIterator");
            for (const node of nodes) {
                const blockWidget = node.widgets?.find(w => w.name === "block");
                if (!blockWidget?.value) continue;

                // Update image preview
                if (data.image && node.imageEl) {
                    node.imageEl.src = `data:image/png;base64,${data.image}`;
                }

                // Update text widget with filename (if empty)
                const textWidget = node.widgets?.find(w => w.name === "text");
                if (textWidget && !textWidget.value) {
                    textWidget.value = data.filename || "";
                }

                // Update counter display
                if (node.counterEl) {
                    node.counterEl.textContent = `Image ${data.index + 1} of ${data.total}`;
                }

                // Reset ready state
                const readyWidget = node.widgets?.find(w => w.name === "ready");
                if (readyWidget) {
                    readyWidget.value = false;
                }

                // Highlight node
                node.bgcolor = "#335533";
            }
            app.graph.setDirtyCanvas(true);
        });
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ImageTextIterator") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                const node = this;

                // Hide ready checkbox
                const readyWidget = node.widgets?.find(w => w.name === "ready");
                if (readyWidget) {
                    readyWidget.type = "hidden";
                    readyWidget.computeSize = () => [0, -4];
                }

                // Create image preview element
                const imgContainer = document.createElement("div");
                imgContainer.style.cssText = "width:100%;display:flex;flex-direction:column;align-items:center;padding:5px;";

                const img = document.createElement("img");
                img.style.cssText = "max-width:100%;max-height:300px;border-radius:4px;margin-bottom:5px;";
                img.src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
                node.imageEl = img;
                imgContainer.appendChild(img);

                // Counter display
                const counter = document.createElement("div");
                counter.style.cssText = "font-size:12px;color:#aaa;margin-bottom:5px;";
                counter.textContent = "Image 0 of 0";
                node.counterEl = counter;
                imgContainer.appendChild(counter);

                // Add image widget
                const imgWidget = node.addDOMWidget("image_preview", "div", imgContainer, {
                    serialize: false,
                });
                imgWidget.computeSize = () => [node.size[0], 320];

                // Add Continue button
                const continueBtn = node.addWidget("button", "continue_btn", "Continue", () => {
                    const indexWidget = node.widgets?.find(w => w.name === "index");
                    const readyWidget = node.widgets?.find(w => w.name === "ready");

                    if (readyWidget) {
                        readyWidget.value = true;
                    }

                    node.bgcolor = null;
                    app.queuePrompt(0, 1);
                });
                continueBtn.serialize = false;

                // Add Next button (increment index after processing)
                const nextBtn = node.addWidget("button", "next_btn", "Next Image", () => {
                    const indexWidget = node.widgets?.find(w => w.name === "index");
                    if (indexWidget) {
                        indexWidget.value = (indexWidget.value || 0) + 1;
                    }
                    // Clear text for next image
                    const textWidget = node.widgets?.find(w => w.name === "text");
                    if (textWidget) {
                        textWidget.value = "";
                    }
                    app.graph.setDirtyCanvas(true);
                });
                nextBtn.serialize = false;

                // Set default size
                node.setSize([350, 550]);
            };

            // Update preview after execution
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                if (message?.image?.[0] && this.imageEl) {
                    this.imageEl.src = `data:image/png;base64,${message.image[0]}`;
                }
                if (message?.index !== undefined && message?.total !== undefined && this.counterEl) {
                    this.counterEl.textContent = `Image ${message.index[0] + 1} of ${message.total[0]}`;
                }

                const readyWidget = this.widgets?.find(w => w.name === "ready");
                if (readyWidget) {
                    readyWidget.value = false;
                }
                this.bgcolor = null;
                app.graph.setDirtyCanvas(true);
            };
        }
    },
});

// TextInputPause extension - handles blocking mode and widget population
app.registerExtension({
    name: "comfyui-text-templates.TextInputPause",
    async setup() {
        // Listen for text_input_pause_update messages from the server
        api.addEventListener("text_input_pause_update", (event) => {
            const data = event.detail;
            if (data?.text !== undefined) {
                // Find all TextInputPause nodes and update them
                const nodes = app.graph._nodes.filter(n => n.type === "TextInputPause");
                for (const node of nodes) {
                    // Only update nodes that have blocking enabled
                    const blockWidget = node.widgets?.find(w => w.name === "block");
                    if (!blockWidget?.value) continue;

                    // Find the text widget and update it
                    const textWidget = node.widgets?.find(w => w.name === "text");
                    if (textWidget) {
                        textWidget.value = data.text;
                    }

                    // Reset ready state
                    const readyWidget = node.widgets?.find(w => w.name === "ready");
                    if (readyWidget) {
                        readyWidget.value = false;
                    }

                    // Visual feedback - highlight the node to show it's waiting
                    node.bgcolor = "#553333";
                }
                app.graph.setDirtyCanvas(true);
            }
        });
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TextInputPause") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                const node = this;

                // Hide the ready checkbox - we'll use a button instead
                const readyWidget = node.widgets?.find(w => w.name === "ready");
                if (readyWidget) {
                    readyWidget.type = "hidden";
                    readyWidget.computeSize = () => [0, -4];
                }

                // Add Continue button
                const continueBtn = node.addWidget("button", "continue_btn", "Continue", () => {
                    // Set ready to true
                    const readyWidget = node.widgets?.find(w => w.name === "ready");
                    if (readyWidget) {
                        readyWidget.value = true;
                    }

                    // Clear the highlight
                    node.bgcolor = null;

                    // Queue the prompt
                    app.queuePrompt(0, 1);
                });
                continueBtn.serialize = false;

                // Make the text widget larger by default
                const textWidget = node.widgets?.find(w => w.name === "text");
                if (textWidget) {
                    node.setSize([node.size[0], 220]);
                }
            };

            // Reset state after execution completes
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                // Reset ready and clear highlight after successful execution
                const readyWidget = this.widgets?.find(w => w.name === "ready");
                if (readyWidget) {
                    readyWidget.value = false;
                }
                this.bgcolor = null;
                app.graph.setDirtyCanvas(true);
            };
        }
    },
});
