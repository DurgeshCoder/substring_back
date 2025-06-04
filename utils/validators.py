from django.core.exceptions import ValidationError
from PIL import Image


class ImageSizeValidator:
    """
    Validates the size of an uploaded image.
    """

    def __init__(self, max_size_kb):
        self.max_size_kb = max_size_kb

    def __call__(self, image):
        if image.size > self.max_size_kb * 1024:
            raise ValidationError(f"Image size should not exceed {self.max_size_kb}KB.")

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.max_size_kb],
            {},
        )


class ImageDimensionsValidator:
    """
    Validates the dimensions of an uploaded image.
    """

    def __init__(self, max_width=1920, max_height=1080):
        self.max_width = max_width
        self.max_height = max_height

    def __call__(self, image):
        img = Image.open(image)
        if img.width > self.max_width or img.height > self.max_height:
            raise ValidationError(
                f"Image dimensions should not exceed {self.max_width}x{self.max_height} pixels."
            )

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.max_width, self.max_height],
            {},
        )


class SquareImageValidator:
    """
    Validates that the uploaded image has square dimensions.
    """

    def __call__(self, image):
        img = Image.open(image)
        if img.width != img.height:
            raise ValidationError("Image must be square (width and height should be equal).")

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [],
            {},
        )


class DynamicImageValidator:
    """
    Combines size and dimension validation for an uploaded image.
    """

    def __init__(self, max_size_kb=1024, max_width=1920, max_height=1080):
        self.max_size_kb = max_size_kb
        self.max_width = max_width
        self.max_height = max_height

    def __call__(self, image):
        ImageSizeValidator(self.max_size_kb)(image)
        ImageDimensionsValidator(self.max_width, self.max_height)(image)

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.max_size_kb, self.max_width, self.max_height],
            {},
        )


class SquareImageWithSizeValidator:
    """
    Combines size and square shape validation for an uploaded image.
    """

    def __init__(self, max_size_kb):
        self.max_size_kb = max_size_kb

    def __call__(self, image):
        ImageSizeValidator(self.max_size_kb)(image)
        SquareImageValidator()(image)

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.max_size_kb],
            {},
        )
