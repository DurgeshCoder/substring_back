import os
from django.conf import settings
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt


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
