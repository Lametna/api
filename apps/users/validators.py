import os
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

def validate_image_file(file: UploadedFile, max_size_mb: int, allowed_extensions: list):
    """
    Validates uploaded image files for size and extension.
    """
    if not file:
        raise ValidationError("No file provided.")

    # 1. Size Validation
    max_bytes = max_size_mb * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"File size exceeds the {max_size_mb}MB limit.")

    # 2. Extension Validation
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}")

    # 3. Pillow Validation (Verify it's actually an image, not a renamed PDF)
    try:
        from PIL import Image
        img = Image.open(file)
        img.verify() # Verify it's an image
        file.seek(0) # Reset pointer after reading
    except ImportError:
        # Pillow not installed, skipping deep validation
        pass
    except Exception:
        raise ValidationError("Invalid or corrupted image file.")

def validate_avatar_image(file: UploadedFile):
    """Avatar specific validation: max 5MB, square-ish recommended."""
    validate_image_file(file, max_size_mb=5, allowed_extensions=['.jpg', '.jpeg', '.png', '.webp'])

def validate_banner_image(file: UploadedFile):
    """Banner specific validation: max 10MB."""
    validate_image_file(file, max_size_mb=10, allowed_extensions=['.jpg', '.jpeg', '.png', '.webp'])
