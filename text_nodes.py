class TextBox:
    """
    Simple text input node. Enter text and output it as a string.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "text"

    def execute(self, text):
        return (text,)


class TextInputPause:
    """
    Text input node with optional blocking for manual editing.

    When 'block' is enabled, the workflow pauses until you check 'ready'.
    Use this to add custom context per image when batch processing.

    Usage:
    1. Connect text_input (e.g., filename from LoadImagesFromFolder)
    2. Enable 'block' to pause for editing
    3. Run workflow - it pauses and populates the text widget
    4. Edit the text to add your context
    5. Check 'ready' and queue again to continue
    6. After completion, uncheck 'ready' for the next image
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "block": ("BOOLEAN", {"default": False}),
                "ready": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "text_input": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "text"
    OUTPUT_NODE = True

    def execute(self, text, block, ready, text_input=None):
        if not block:
            # Blocking disabled - pass through input or use widget text
            output_text = text_input if text_input is not None else text
        elif not ready:
            # Blocking enabled but not ready - pause for editing
            from server import PromptServer
            from comfy.model_management import InterruptProcessingException

            # Send input text to frontend to populate the widget
            PromptServer.instance.send_sync("text_input_pause_update", {
                "text": text_input if text_input is not None else text,
            })

            raise InterruptProcessingException()
        else:
            # Blocking enabled and ready - use the edited text
            output_text = text if text else (text_input or "")

        return {"ui": {"text": [output_text]}, "result": (output_text,)}


class ShowText:
    """
    Display text input. Useful for viewing text output from other nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "text"
    OUTPUT_NODE = True

    def execute(self, text):
        return {"ui": {"text": [text]}, "result": (text,)}
