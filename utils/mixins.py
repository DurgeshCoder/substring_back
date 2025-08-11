from django.db import models


class FileCleanupMixin(models.Model):
    """
    Mixin to:
      - delete old files when a file field is updated
      - delete files from storage when the instance is deleted

    How to use:
      - In your model, set: file_fields = ["image", "file", ...]
      - Inherit from FileCleanupMixin before models.Model

    Notes:
      - Works with any Django Storage backend (local, S3, etc.).
      - Safe when field is unchanged (compares names).
    """
    # Override in subclasses with the names of FileField/ImageField attributes
    file_fields: list[str] = []

    class Meta:
        abstract = True

    def _get_old_instance(self):
        if not self.pk:
            return None
        try:
            return self.__class__.objects.get(pk=self.pk)
        except self.__class__.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        old = self._get_old_instance()
        super().save(*args, **kwargs)  # Save first so new files have names

        # If there was an old instance, remove replaced files
        if old:
            for field_name in getattr(self, "file_fields", []):
                old_file = getattr(old, field_name, None)
                new_file = getattr(self, field_name, None)

                # If the file changed (different storage path), delete the old one
                if getattr(old_file, "name", None) and (
                        not new_file or old_file.name != getattr(new_file, "name", None)
                ):
                    try:
                        old_file.storage.delete(old_file.name)
                    except Exception:
                        # Swallow errors to avoid breaking saves; log if you have logging
                        pass

    def delete(self, *args, **kwargs):
        # Clean up files on delete
        for field_name in getattr(self, "file_fields", []):
            f = getattr(self, field_name, None)
            if getattr(f, "name", None):
                try:
                    f.storage.delete(f.name)
                except Exception:
                    pass
        super().delete(*args, **kwargs)
