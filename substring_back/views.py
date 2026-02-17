import os
from datetime import datetime
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework_simplejwt.views import TokenObtainPairView

from substring_back.serializers import CustomTokenObtainPairSerializer, UserSerializer
from rest_framework import generics, filters


class UserDetailView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']


# Generate token view


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# END

@csrf_exempt
def delete_image(request):
    """
    Deletes an image and its thumbnail (if any), and cleans up empty directories.
    """
    if request.method == 'POST':
        try:
            # Parse JSON request body
            data = json.loads(request.body)
            image_path = data.get('file_path')

            if not image_path:
                return JsonResponse({'success': False, 'message': 'file_path is required'}, status=400)

            # Remove MEDIA_URL from file_path if it exists
            if image_path.startswith(settings.MEDIA_URL):
                image_path = image_path.replace(settings.MEDIA_URL, '', 1)

            # Build the full path to the image
            full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # Check and delete the main image file
            if os.path.exists(full_image_path):
                os.remove(full_image_path)
                print(f"Deleted main image: {full_image_path}")
            else:
                return JsonResponse({'success': False, 'message': 'File not found.'}, status=404)

            # Attempt to delete the thumbnail (if any)
            thumbnail_path = get_thumbnail_path(full_image_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                print(f"Deleted thumbnail: {thumbnail_path}")

            # Clean up empty directories
            parent_folder = os.path.dirname(full_image_path)
            delete_empty_folders(parent_folder)

            return JsonResponse({'success': True, 'message': 'Image and associated files deleted successfully.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


def get_thumbnail_path(full_image_path):
    """
    Constructs the thumbnail file path by appending '_thumb' before the file extension.
    Example:
        Input: '/path/to/image.jpg'
        Output: '/path/to/image_thumb.jpg'
    """
    directory, file_name = os.path.split(full_image_path)
    name, ext = os.path.splitext(file_name)
    thumbnail_file_name = f"{name}_thumb{ext}"
    return os.path.join(directory, thumbnail_file_name)


def delete_empty_folders(path):
    """
    Recursively deletes empty folders starting from the given path.
    """
    if not os.path.isdir(path):
        return

    # Check if the folder is empty
    if not os.listdir(path):
        os.rmdir(path)  # Remove the folder
        print(f"Deleted empty folder: {path}")

        # Recursively check the parent folder
        parent_folder = os.path.dirname(path)
        delete_empty_folders(parent_folder)


# ekeditor image upload view

# --- Validation limits ---
MAX_BYTES = 500 * 1024  # 500 KB
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}


# rename path function
def _dated_path(bucket: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    date_dir = datetime.now().strftime("%Y/%m/%d")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{base}_{stamp}{ext.lower()}"
    rel_path = os.path.join(settings.CKEDITOR_UPLOAD_PATH, bucket, date_dir, safe_name)
    return rel_path.replace("\\", "/")


# ekeidtor error function
def _ckeditor_error(func_num: str | None, message: str):
    """Return an error CKEditor understands."""
    if func_num:
        return HttpResponse(
            f"<script>window.parent.CKEDITOR.tools.callFunction({func_num}, '', '{message}');</script>",
            content_type="text/html",
            status=400
        )
    return JsonResponse({"uploaded": 0, "error": {"message": message}}, status=400)


# validator image
def _validate_image(file_obj, filename: str) -> bytes:
    """Validate size, format, and dimensions. Return image bytes if valid."""
    # 1) Size check
    if getattr(file_obj, "size", None) and file_obj.size > MAX_BYTES:
        raise ValueError(f"File too large. Must be ≤ {MAX_BYTES // 1024} KB.")

    # 2) Extension check
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"Unsupported file type: {ext}")

    # 3) Load into Pillow to verify image and check dimensions
    raw = file_obj.read()
    try:
        img = Image.open(BytesIO(raw))
        img.load()
    except UnidentifiedImageError:
        raise ValueError("Invalid image file.")

    fmt = (img.format or "").upper()
    if fmt not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported image format: {fmt}")

    width, height = img.size
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise ValueError(f"Image dimensions too large. Max {MAX_WIDTH}×{MAX_HEIGHT}px.")

    return raw


@csrf_exempt
@require_POST
def ckeditor_custom_upload(request, bucket: str):
    """CKEditor custom image/file upload with validation."""
    f = request.FILES.get("upload") or request.FILES.get("file") or request.FILES.get("image")
    if not f:
        return HttpResponseBadRequest("No file part")

    func_num = request.GET.get("CKEditorFuncNum")

    # Validate image
    try:
        cleaned_bytes = _validate_image(f, f.name)
    except ValueError as e:
        return _ckeditor_error(func_num, str(e))

    # Save file
    rel_path = _dated_path(bucket, f.name)
    saved_path = default_storage.save(rel_path, ContentFile(cleaned_bytes))
    url = f"{settings.MEDIA_URL}{saved_path}"

    # CKEditor iframe mode
    if func_num:
        return HttpResponse(
            f"<script>window.parent.CKEDITOR.tools.callFunction({func_num}, '{url}', '');</script>",
            content_type="text/html"
        )

    # CKEditor XHR mode
    return JsonResponse({"uploaded": 1, "fileName": os.path.basename(saved_path), "url": url})
