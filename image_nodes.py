import os
import io
import base64
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
                "limit": ("INT", {"default": 0, "min": 0, "max": 10000}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("images", "filenames", "count")
    OUTPUT_IS_LIST = (True, True, False)
    FUNCTION = "load_images"
    CATEGORY = "image"

    def load_images(self, folder_path, extension_filter="", limit=0):
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

        # Apply limit if specified (0 = no limit)
        if limit > 0:
            image_files = image_files[:limit]

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
            # Each image as individual tensor with batch dim (1, H, W, C)
            img_tensor = torch.from_numpy(img_array).unsqueeze(0)
            images.append(img_tensor)

            # Filename without extension
            filenames.append(os.path.splitext(filename)[0])

        return (images, filenames, len(filenames))


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


class SaveImagesToFolder:
    """
    Save images to a folder with specified filenames. Supports batch processing.
    Useful for creating updated datasets via I2I workflows.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "output_folder": ("STRING", {"default": "", "multiline": False}),
                "filename": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "format": (["png", "jpg", "webp"], {"default": "png"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepaths",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "save_images"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def save_images(self, images, output_folder, filename, format=None, quality=None):
        # Handle format default and list format
        if format is None or len(format) == 0:
            format = ["png"]
        fmt = format[0] if isinstance(format, list) else format

        # Handle quality
        if quality is None or len(quality) == 0:
            quality = [95]
        qual = quality[0] if isinstance(quality, list) else quality

        # Get output folder (take first if list)
        out_folder = output_folder[0] if isinstance(output_folder, list) else output_folder
        if not out_folder:
            raise ValueError("Output folder path is required")

        # Create output folder if it doesn't exist
        os.makedirs(out_folder, exist_ok=True)

        # Map format to extension and save options
        format_map = {
            "png": (".png", {}),
            "jpg": (".jpg", {"quality": qual}),
            "webp": (".webp", {"quality": qual}),
        }
        ext, save_opts = format_map.get(fmt, (".png", {}))

        # Process each image/filename pair
        filepaths = []
        for i, (img_tensor, fname) in enumerate(zip(images, filename)):
            # Handle batch dimension - take first image if batched
            if len(img_tensor.shape) == 4:
                img_tensor = img_tensor[0]

            # Convert tensor to PIL Image (HWC format, 0-1 range)
            img_array = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array)

            # Save image
            filepath = os.path.join(out_folder, f"{fname}{ext}")
            img.save(filepath, **save_opts)
            filepaths.append(filepath)

        return (filepaths,)


class ImageTextIterator:
    """
    Browse through images and set text for each before processing.

    Use Prev/Next buttons to browse images and edit text for each.
    The text for each image is stored. When ready, click Continue to
    output all images with their corresponding texts.

    Usage:
    1. Connect images and filenames from LoadImagesFromFolder
    2. Run workflow - shows first image with filename as default text
    3. Use Prev/Next to browse images, edit text for each
    4. Click Continue when all texts are set - outputs all images + texts
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filenames": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "current_text": ("STRING", {"multiline": True, "default": ""}),
                "current_index": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "all_texts": ("STRING", {"default": ""}),
                "ready": ("BOOLEAN", {"default": False}),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT")
    RETURN_NAMES = ("images", "texts", "filenames", "count")
    OUTPUT_IS_LIST = (True, True, True, False)
    FUNCTION = "process"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def process(self, images, filenames, current_text=None, current_index=None, all_texts=None, ready=None):
        import json

        # Handle None defaults and extract scalar values from lists
        if current_index is None:
            current_index = [0]
        if current_text is None:
            current_text = [""]
        if all_texts is None:
            all_texts = [""]
        if ready is None:
            ready = [False]

        idx = current_index[0] if isinstance(current_index, list) else current_index
        cur_txt = current_text[0] if isinstance(current_text, list) else current_text
        all_txt = all_texts[0] if isinstance(all_texts, list) else all_texts
        rdy = ready[0] if isinstance(ready, list) else ready

        total = len(images)
        idx = max(0, min(idx, total - 1))

        # Parse stored texts (JSON array) or initialize
        try:
            texts_array = json.loads(all_txt) if all_txt else []
        except json.JSONDecodeError:
            texts_array = []

        # Ensure array is right size, fill with filenames as defaults
        while len(texts_array) < total:
            default_idx = len(texts_array)
            default_text = filenames[default_idx] if default_idx < len(filenames) else ""
            texts_array.append(default_text)

        # Get current image for preview
        current_image = images[idx]
        current_filename = filenames[idx] if idx < len(filenames) else ""

        # Create base64 preview
        if len(current_image.shape) == 4:
            img_tensor = current_image[0]
        else:
            img_tensor = current_image
        img_array = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_array)

        max_size = 512
        if pil_img.width > max_size or pil_img.height > max_size:
            ratio = min(max_size / pil_img.width, max_size / pil_img.height)
            new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
            pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Send preview to frontend
        from server import PromptServer
        PromptServer.instance.send_sync("image_text_iterator_update", {
            "image": img_base64,
            "filename": current_filename,
            "index": idx,
            "total": total,
            "texts": texts_array,
            "ready": rdy,
        })

        if not rdy:
            # Not ready - block execution, let user browse and edit
            try:
                from comfy_execution.graph import ExecutionBlocker
                return {
                    "ui": {
                        "image": [img_base64],
                        "filename": [current_filename],
                        "index": [idx],
                        "total": [total],
                    },
                    "result": (ExecutionBlocker(None), ExecutionBlocker(None), ExecutionBlocker(None), ExecutionBlocker(None))
                }
            except ImportError:
                import nodes
                nodes.interrupt_processing()
                return {"ui": {}, "result": (images, texts_array, filenames, total)}

        # Ready - output all images with their texts
        return {
            "ui": {
                "image": [img_base64],
                "filename": [current_filename],
                "index": [idx],
                "total": [total],
            },
            "result": (images, texts_array, filenames, total)
        }
