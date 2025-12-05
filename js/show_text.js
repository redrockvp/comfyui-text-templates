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

// ImageTextIterator extension - browse images, set text for each, then output all
app.registerExtension({
    name: "comfyui-text-templates.ImageTextIterator",
    async setup() {
        // Listen for image_text_iterator_update messages
        api.addEventListener("image_text_iterator_update", (event) => {
            const data = event.detail;
            if (!data) return;

            const nodes = app.graph._nodes.filter(n => n.type === "ImageTextIterator");
            for (const node of nodes) {
                // Store data for navigation
                node._iteratorData = data;

                // Update image preview
                if (data.image && node.imageEl) {
                    node.imageEl.src = `data:image/png;base64,${data.image}`;
                }

                // Update counter display
                if (node.counterEl) {
                    node.counterEl.textContent = `Image ${data.index + 1} of ${data.total}`;
                }

                // Update current_text widget with the text for this image
                const currentTextWidget = node.widgets?.find(w => w.name === "current_text");
                if (currentTextWidget && data.texts && data.texts[data.index] !== undefined) {
                    currentTextWidget.value = data.texts[data.index];
                }

                // Store all_texts in hidden widget
                const allTextsWidget = node.widgets?.find(w => w.name === "all_texts");
                if (allTextsWidget && data.texts) {
                    allTextsWidget.value = JSON.stringify(data.texts);
                }

                // Update index widget
                const indexWidget = node.widgets?.find(w => w.name === "current_index");
                if (indexWidget) {
                    indexWidget.value = data.index;
                }

                // Highlight node when waiting for input
                if (!data.ready) {
                    node.bgcolor = "#335533";
                }
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

                // Hide internal widgets (controlled by buttons)
                const widgetsToHide = ["ready", "current_index", "all_texts"];
                for (const widgetName of widgetsToHide) {
                    const widget = node.widgets?.find(w => w.name === widgetName);
                    if (widget) {
                        widget.type = "hidden";
                        widget.computeSize = () => [0, -4];
                    }
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

                // Navigation buttons container
                const navContainer = document.createElement("div");
                navContainer.style.cssText = "display:flex;gap:10px;margin-bottom:5px;";

                const prevBtn = document.createElement("button");
                prevBtn.textContent = "< Prev";
                prevBtn.style.cssText = "padding:5px 15px;cursor:pointer;";
                prevBtn.onclick = () => navigateImage(node, -1);
                navContainer.appendChild(prevBtn);

                const nextBtn = document.createElement("button");
                nextBtn.textContent = "Next >";
                nextBtn.style.cssText = "padding:5px 15px;cursor:pointer;";
                nextBtn.onclick = () => navigateImage(node, 1);
                navContainer.appendChild(nextBtn);

                imgContainer.appendChild(navContainer);

                // Add image widget
                const imgWidget = node.addDOMWidget("image_preview", "div", imgContainer, {
                    serialize: false,
                });
                imgWidget.computeSize = () => [node.size[0], 360];

                // Helper function to navigate images
                function navigateImage(node, direction) {
                    const indexWidget = node.widgets?.find(w => w.name === "current_index");
                    const currentTextWidget = node.widgets?.find(w => w.name === "current_text");
                    const allTextsWidget = node.widgets?.find(w => w.name === "all_texts");

                    if (!indexWidget || !node._iteratorData) return;

                    const currentIdx = indexWidget.value;
                    const total = node._iteratorData.total || 1;

                    // Save current text to all_texts array before navigating
                    let texts = [];
                    try {
                        texts = JSON.parse(allTextsWidget?.value || "[]");
                    } catch (e) {
                        texts = [];
                    }

                    // Ensure array is right size
                    while (texts.length < total) {
                        texts.push("");
                    }

                    // Save current text
                    if (currentTextWidget) {
                        texts[currentIdx] = currentTextWidget.value;
                    }

                    // Calculate new index
                    let newIdx = currentIdx + direction;
                    if (newIdx < 0) newIdx = 0;
                    if (newIdx >= total) newIdx = total - 1;

                    // Update widgets
                    indexWidget.value = newIdx;
                    if (allTextsWidget) {
                        allTextsWidget.value = JSON.stringify(texts);
                    }

                    // Load text for new image
                    if (currentTextWidget) {
                        currentTextWidget.value = texts[newIdx] || "";
                    }

                    // Queue to refresh the image preview
                    app.queuePrompt(0, 1);
                }

                // Add Continue button - outputs all images with their texts
                const continueBtn = node.addWidget("button", "continue_btn", "Continue (Process All)", () => {
                    // Save current text before continuing
                    const indexWidget = node.widgets?.find(w => w.name === "current_index");
                    const currentTextWidget = node.widgets?.find(w => w.name === "current_text");
                    const allTextsWidget = node.widgets?.find(w => w.name === "all_texts");

                    if (indexWidget && currentTextWidget && allTextsWidget) {
                        let texts = [];
                        try {
                            texts = JSON.parse(allTextsWidget.value || "[]");
                        } catch (e) {
                            texts = [];
                        }

                        const currentIdx = indexWidget.value;
                        while (texts.length <= currentIdx) {
                            texts.push("");
                        }
                        texts[currentIdx] = currentTextWidget.value;
                        allTextsWidget.value = JSON.stringify(texts);
                    }

                    // Set ready and queue
                    const readyWidget = node.widgets?.find(w => w.name === "ready");
                    if (readyWidget) {
                        readyWidget.value = true;
                    }
                    node.bgcolor = null;
                    app.queuePrompt(0, 1);
                });
                continueBtn.serialize = false;

                // Add Reset button - clear all texts and go back to first
                const resetBtn = node.addWidget("button", "reset_btn", "Reset All", () => {
                    const indexWidget = node.widgets?.find(w => w.name === "current_index");
                    const currentTextWidget = node.widgets?.find(w => w.name === "current_text");
                    const allTextsWidget = node.widgets?.find(w => w.name === "all_texts");
                    const readyWidget = node.widgets?.find(w => w.name === "ready");

                    if (indexWidget) indexWidget.value = 0;
                    if (currentTextWidget) currentTextWidget.value = "";
                    if (allTextsWidget) allTextsWidget.value = "";
                    if (readyWidget) readyWidget.value = false;

                    node._iteratorData = null;
                    node.bgcolor = null;
                    app.graph.setDirtyCanvas(true);
                });
                resetBtn.serialize = false;

                // Set default size
                node.setSize([350, 580]);
            };

            // After execution completes
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                // Update preview from message
                if (message?.image?.[0] && this.imageEl) {
                    this.imageEl.src = `data:image/png;base64,${message.image[0]}`;
                }
                if (message?.index !== undefined && message?.total !== undefined && this.counterEl) {
                    const currentIdx = message.index[0];
                    const total = message.total[0];
                    this.counterEl.textContent = `Image ${currentIdx + 1} of ${total}`;
                }

                // Reset ready state after processing completes
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
