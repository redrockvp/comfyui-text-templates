from .text_template import TextTemplate
from .text_nodes import TextBox, ShowText
from .image_nodes import LoadImagesFromFolder, SaveTextToFile, SaveImagesToFolder

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
    "TextBox": TextBox,
    "ShowText": ShowText,
    "LoadImagesFromFolder": LoadImagesFromFolder,
    "SaveTextToFile": SaveTextToFile,
    "SaveImagesToFolder": SaveImagesToFolder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "Text Template",
    "TextBox": "Text Box",
    "ShowText": "Show Text",
    "LoadImagesFromFolder": "Load Images From Folder",
    "SaveTextToFile": "Save Text To File",
    "SaveImagesToFolder": "Save Images To Folder",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
