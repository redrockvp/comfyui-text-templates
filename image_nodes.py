import os
from PIL import Image
import numpy as np
import torch

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}

# Global state to track current index per folder
_folder_indices = {}


class LoadImagesFromFolder:
    """
    Load images from a folder one at a time, outputting the image and its filename.
    Each queue run advances to the next image in the folder.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "", "multiline": False}),
                "index": ("INT", {"default": 0, "min": 0, "max": 99999}),
            },
            "optional": {
                "extension_filter": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT")
    RETURN_NAMES = ("image", "filename", "filename_with_ext", "total_images")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def load_image(self, folder_path, index, extension_filter=""):
        if not folder_path or not os.path.isdir(folder_path):
            raise ValueError(f"Invalid folder path: {folder_path}")

        # Get list of image files
        image_files = []

        # Parse extension filter
        if extension_filter.strip():
            allowed_exts = {f".{ext.strip().lower().lstrip('.')}" for ext in extension_filter.split(',')}
        else:
            allowed_exts = IMAGE_EXTENSIONS

        for filename in sorted(os.listdir(folder_path)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in allowed_exts:
                image_files.append(filename)

        if not image_files:
            raise ValueError(f"No image files found in: {folder_path}")

        total_images = len(image_files)

        # Clamp index to valid range
        current_index = index % total_images

        # Get the current image
        current_filename = image_files[current_index]
        filepath = os.path.join(folder_path, current_filename)

        # Load image
        img = Image.open(filepath)
        img = img.convert("RGB")

        # Convert to tensor (ComfyUI format: BHWC, float32, 0-1 range)
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)  # Add batch dimension

        # Get filename without extension
        filename_no_ext = os.path.splitext(current_filename)[0]

        return (img_tensor, filename_no_ext, current_filename, total_images)


class SaveTextToFile:
    """
    Save text content to a file. Useful for saving captions or other text outputs.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "output_folder": ("STRING", {"default": "", "multiline": False}),
                "filename": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "extension": ("STRING", {"default": ".txt", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepath",)
    FUNCTION = "save_text"
    CATEGORY = "text"
    OUTPUT_NODE = True

    def save_text(self, text, output_folder, filename, extension=".txt"):
        if not output_folder:
            raise ValueError("Output folder path is required")

        # Ensure extension starts with a dot
        if extension and not extension.startswith('.'):
            extension = '.' + extension

        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Build full filepath
        filepath = os.path.join(output_folder, f"{filename}{extension}")

        # Write text to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        return (filepath,)
