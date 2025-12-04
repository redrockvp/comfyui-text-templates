class TextTemplate:
    """
    Compose text by injecting wired text inputs into an editable template.
    For chaining LM Studio outputs and building context.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "multiline": True,
                    "default": "Use {1}, {2}, etc. as placeholders"
                }),
            },
            "optional": {
                "text_1": ("STRING", {"forceInput": True}),
                "text_2": ("STRING", {"forceInput": True}),
                "text_3": ("STRING", {"forceInput": True}),
                "text_4": ("STRING", {"forceInput": True}),
                "text_5": ("STRING", {"forceInput": True}),
                "text_6": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "text"

    def execute(self, template, text_1=None, text_2=None, text_3=None,
                text_4=None, text_5=None, text_6=None):
        result = template

        inputs = {
            "1": text_1,
            "2": text_2,
            "3": text_3,
            "4": text_4,
            "5": text_5,
            "6": text_6,
        }

        for key, value in inputs.items():
            if value is not None:
                result = result.replace(f"{{{key}}}", value)

        return (result,)
