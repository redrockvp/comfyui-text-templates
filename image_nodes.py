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
    Iterate through a batch of images one at a time with text editing.
    Shows a preview of the current image and allows editing context text.

    Usage:
    1. Connect images and filenames from LoadImagesFromFolder
    2. Enable 'block' to pause on each image
    3. Run workflow - shows first image preview with filename
    4. Edit the text to add context
    5. Click Continue to process this image and move to the next
    6. Repeat until all images are processed
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filenames": ("STRING", {"forceInput": True}),
                "index": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "text": ("STRING", {"multiline": True, "default": ""}),
                "block": ("BOOLEAN", {"default": True}),
                "ready": ("BOOLEAN", {"default": False}),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "text", "index", "total")
    FUNCTION = "iterate"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def iterate(self, images, filenames, index, text, block, ready):
        # Extract scalar values from lists
        idx = index[0] if isinstance(index, list) else index
        txt = text[0] if isinstance(text, list) else text
        blk = block[0] if isinstance(block, list) else block
        rdy = ready[0] if isinstance(ready, list) else ready

        total = len(images)

        # Clamp index to valid range
        idx = max(0, min(idx, total - 1))

        # Get current image and filename
        current_image = images[idx]
        current_filename = filenames[idx] if idx < len(filenames) else ""

        # Create base64 preview of current image
        if len(current_image.shape) == 4:
            img_tensor = current_image[0]
        else:
            img_tensor = current_image
        img_array = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_array)

        # Resize for preview (max 512px)
        max_size = 512
        if pil_img.width > max_size or pil_img.height > max_size:
            ratio = min(max_size / pil_img.width, max_size / pil_img.height)
            new_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
            pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        if blk and not rdy:
            # Blocking mode, not ready - pause for editing
            from server import PromptServer
            import execution

            # Send image preview and filename to frontend
            PromptServer.instance.send_sync("image_text_iterator_update", {
                "image": img_base64,
                "filename": current_filename,
                "index": idx,
                "total": total,
            })

            raise execution.InterruptProcessingException()

        # Ready to output - use edited text (or filename if empty)
        output_text = txt if txt else current_filename

        return {
            "ui": {
                "image": [img_base64],
                "filename": [current_filename],
                "index": [idx],
                "total": [total],
            },
            "result": (current_image, output_text, idx, total)
        }
