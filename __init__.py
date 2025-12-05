from .text_template import TextTemplate
from .text_nodes import TextBox, ShowText, TextInputPause
from .image_nodes import LoadImagesFromFolder, SaveTextToFile, SaveImagesToFolder, ImageTextIterator

NODE_CLASS_MAPPINGS = {
    "TextTemplate": TextTemplate,
    "TextBox": TextBox,
    "ShowText": ShowText,
    "TextInputPause": TextInputPause,
    "LoadImagesFromFolder": LoadImagesFromFolder,
    "SaveTextToFile": SaveTextToFile,
    "SaveImagesToFolder": SaveImagesToFolder,
    "ImageTextIterator": ImageTextIterator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextTemplate": "Text Template",
    "TextBox": "Text Box",
    "ShowText": "Show Text",
    "TextInputPause": "Text Input (Pause)",
    "LoadImagesFromFolder": "Load Images From Folder",
    "SaveTextToFile": "Save Text To File",
    "SaveImagesToFolder": "Save Images To Folder",
    "ImageTextIterator": "Image Text Iterator",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
