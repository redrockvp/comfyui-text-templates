from .text_template import TextTemplate
from .text_nodes import TextBox, ShowText

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
    "TextBox": TextBox,
    "ShowText": ShowText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "Text Template",
    "TextBox": "Text Box",
    "ShowText": "Show Text",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
