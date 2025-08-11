# utils/file_upload.py
import os
from datetime import datetime
from django.utils.deconstruct import deconstructible

@deconstructible
class AppendDateToFilename:
    def __init__(self, folder_name="uploads", with_time=True):
        self.folder_name = folder_name
        self.with_time = with_time

    def __call__(self, instance, filename):
        name, ext = os.path.splitext(filename)
        fmt = "%Y%m%d_%H%M%S" if self.with_time else "%Y%m%d"
        stamp = datetime.now().strftime(fmt)
        new_name = f"{name}_{stamp}{ext.lower()}"
        return os.path.join(self.folder_name, new_name).replace("\\", "/")