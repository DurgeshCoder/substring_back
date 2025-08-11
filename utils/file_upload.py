import os
from datetime import datetime


def append_date_to_filename(folder_name="uploads"):
    """
    Returns a function that appends the current date to the uploaded file's name.
    Can be reused in any model.

    Example usage in model:
        image = models.ImageField(upload_to=append_date_to_filename("images"))
    """

    def wrapper(instance, filename):
        # Extract original name and extension
        name, ext = os.path.splitext(filename)

        # Add current date
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{name}_{date_str}{ext}"

        # Store in given folder
        return os.path.join(folder_name, new_filename)

    return wrapper
