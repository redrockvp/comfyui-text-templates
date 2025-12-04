from .text_template import TextTemplate

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "Text Template",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
