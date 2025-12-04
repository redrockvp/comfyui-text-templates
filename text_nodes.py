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
