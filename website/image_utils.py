import io
import os
import uuid
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

MAX_UPLOAD_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB max per original photo
ALLOWED_PIL_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'ICO'}


def validate_uploaded_image_strict(file_obj, max_bytes=MAX_UPLOAD_IMAGE_BYTES):
    """
    Strictly validate an uploaded image file by:
    1. Checking file size (default max 8 MB).
    2. Opening and verifying the image stream with Pillow (rejecting non-image or corrupt files).
    Returns (pil_format, width, height).
    """
    if not file_obj:
        raise ValidationError("No image file provided.")

    file_size = getattr(file_obj, 'size', None)
    if file_size is not None and file_size > max_bytes:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)
        raise ValidationError(f"File size ({size_mb:.1f} MB) exceeds the {max_mb:.0f} MB maximum limit.")

    try:
        file_obj.seek(0)
        raw_bytes = file_obj.read()
        file_obj.seek(0)
    except Exception as exc:
        raise ValidationError(f"Could not read uploaded file: {exc}")

    if len(raw_bytes) > max_bytes:
        size_mb = len(raw_bytes) / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)
        raise ValidationError(f"File size ({size_mb:.1f} MB) exceeds the {max_mb:.0f} MB maximum limit.")

    if len(raw_bytes) == 0:
        raise ValidationError("Uploaded file is empty.")

    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            pil_format = (img.format or '').upper()
            width, height = img.size
            img.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise ValidationError("Invalid or corrupted image file. Allowed types: JPG, PNG, WEBP.")

    if pil_format not in ALLOWED_PIL_FORMATS:
        raise ValidationError(f"Unsupported image format '{pil_format}'. Allowed types: JPG, PNG, WEBP.")

    return raw_bytes, pil_format, width, height


def generate_image_variants(file_obj, max_bytes=MAX_UPLOAD_IMAGE_BYTES):
    """
    Validate image with Pillow, apply EXIF transpose, strip metadata, and generate:
    - clean_file: sanitized main image ContentFile with randomized UUID name
    - grid_file: 800px max longest-side WebP/JPEG ContentFile
    - large_file: 1600px max longest-side WebP/JPEG ContentFile
    """
    raw_bytes, pil_format, width, height = validate_uploaded_image_strict(file_obj, max_bytes=max_bytes)

    with Image.open(io.BytesIO(raw_bytes)) as src_img:
        try:
            transposed = ImageOps.exif_transpose(src_img)
        except Exception:
            transposed = src_img.copy()

        # Convert to RGB/RGBA to strip metadata and ensure WebP/JPEG compatibility
        if transposed.mode in ('RGBA', 'LA') or (transposed.mode == 'P' and 'transparency' in transposed.info):
            base_img = transposed.convert('RGBA')
            out_format = 'WEBP'
            ext = '.webp'
        else:
            base_img = transposed.convert('RGB')
            out_format = 'WEBP'
            ext = '.webp'

        # 1. Large variant (max 1600px longest side)
        large_img = base_img.copy()
        if max(large_img.size) > 1600:
            large_img.thumbnail((1600, 1600), Image.Resampling.BILINEAR)
        large_buf = io.BytesIO()
        large_img.save(large_buf, format=out_format, quality=85, method=1)
        large_bytes = large_buf.getvalue()

        # 2. Grid variant (max 800px longest side)
        grid_img = large_img.copy()
        if max(grid_img.size) > 800:
            grid_img.thumbnail((800, 800), Image.Resampling.BILINEAR)
        grid_buf = io.BytesIO()
        grid_img.save(grid_buf, format=out_format, quality=82, method=1)
        grid_bytes = grid_buf.getvalue()

        # 3. Clean main image (max 2000px longest side, metadata stripped)
        if max(base_img.size) <= 1600:
            main_bytes = large_bytes
        else:
            main_img = base_img.copy()
            if max(main_img.size) > 2000:
                main_img.thumbnail((2000, 2000), Image.Resampling.BILINEAR)
            main_buf = io.BytesIO()
            main_img.save(main_buf, format=out_format, quality=86, method=1)
            main_bytes = main_buf.getvalue()

    raw_name = os.path.splitext(os.path.basename(getattr(file_obj, 'name', '') or 'Photo'))[0]
    original_stem = raw_name.replace('_', ' ').replace('-', ' ').strip().title() or 'Gallery Photo'
    uid = uuid.uuid4().hex
    clean_file = ContentFile(main_bytes, name=f"{uid}{ext}")
    grid_file = ContentFile(grid_bytes, name=f"grid_{uid}{ext}")
    large_file = ContentFile(large_bytes, name=f"large_{uid}{ext}")
    return {
        'clean_file': clean_file,
        'grid_file': grid_file,
        'large_file': large_file,
        'original_stem': original_stem,
    }

