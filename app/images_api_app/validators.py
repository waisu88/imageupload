from django.core.validators import RegexValidator

charfield_image_validator = RegexValidator(r"^[a-zA-Z0-9-]*$", "Only letters, numbers and hyphens are available.")
