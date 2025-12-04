import os
from PIL import Image
import numpy as np
import torch

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}


class LoadImagesFromFolder:
    """
    Load ALL images from a folder as a batch, with corresponding filenames.
    Images are resized to match the first image's dimensions for batching.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "extension_filter": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("images", "filenames", "count")
    OUTPUT_IS_LIST = (False, True, False)
    FUNCTION = "load_images"
    CATEGORY = "image"

    def load_images(self, folder_path, extension_filter=""):
        if not folder_path or not os.path.isdir(folder_path):
            raise ValueError(f"Invalid folder path: {folder_path}")

        # Parse extension filter
        if extension_filter.strip():
            allowed_exts = {f".{ext.strip().lower().lstrip('.')}" for ext in extension_filter.split(',')}
        else:
            allowed_exts = IMAGE_EXTENSIONS

        # Get list of image files
        image_files = []
        for filename in sorted(os.listdir(folder_path)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in allowed_exts:
                image_files.append(filename)

        if not image_files:
            raise ValueError(f"No image files found in: {folder_path}")

        # Load all images
        images = []
        filenames = []
        target_size = None

        for filename in image_files:
            filepath = os.path.join(folder_path, filename)
            img = Image.open(filepath)
            img = img.convert("RGB")

            # Use first image's size as target, resize others to match
            if target_size is None:
                target_size = img.size
            elif img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)

            img_array = np.array(img).astype(np.float32) / 255.0
            images.append(img_array)

            # Filename without extension
            filenames.append(os.path.splitext(filename)[0])

        # Stack into batch tensor (BHWC format)
        batch_tensor = torch.from_numpy(np.stack(images, axis=0))

        return (batch_tensor, filenames, len(filenames))


class SaveTextToFile:
    """
    Save text content to a file. Supports batch processing with lists.
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

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepaths",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "save_text"
    CATEGORY = "text"
    OUTPUT_NODE = True

    def save_text(self, text, output_folder, filename, extension=None):
        # Handle extension default and list format
        if extension is None or len(extension) == 0:
            extension = [".txt"]

        # Get the actual extension value (take first if list)
        ext = extension[0] if isinstance(extension, list) else extension
        if ext and not ext.startswith('.'):
            ext = '.' + ext

        # Get output folder (take first if list)
        out_folder = output_folder[0] if isinstance(output_folder, list) else output_folder
        if not out_folder:
            raise ValueError("Output folder path is required")

        # Create output folder if it doesn't exist
        os.makedirs(out_folder, exist_ok=True)

        # Process each text/filename pair
        filepaths = []
        for i, (txt, fname) in enumerate(zip(text, filename)):
            filepath = os.path.join(out_folder, f"{fname}{ext}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(txt)
            filepaths.append(filepath)

        return (filepaths,)
