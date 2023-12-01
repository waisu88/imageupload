from django.db import models
from django.contrib.auth.models import User

from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from .validators import charfield_image_validator

from django.db.models.signals import post_delete
from django.dispatch import receiver


class Image(models.Model):
    """
    Represents an image uploaded by an user.
    """
    name = models.CharField(max_length=40, validators=[charfield_image_validator])
    slug = models.SlugField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/%Y/%m/%d/', max_length=100, 
                              validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    created_at = models.DateTimeField(auto_now_add=True)

@receiver(post_delete, sender=Image)
def delete_expiring_link_image(sender, instance, **kwargs):
    """
    Signal handler to delete associated image file when an Image instance is deleted.
    """
    instance.image.delete(False) 


class Thumbnail(models.Model):
    """
    Represents a thumbnail associated with a base image.
    """
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    base_image = models.ForeignKey(Image, related_name='thumbnails', on_delete=models.CASCADE)
    thumbnail_image = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', max_length=100)
    thumbnail_size = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thumbnail of {self.base_image.name} {self.thumbnail_size} size"

@receiver(post_delete, sender=Thumbnail)
def delete_expiring_link_image(sender, instance, **kwargs):
    """
    Signal handler to delete associated thumbnail image file when a Thumbnail instance is deleted.
    """
    instance.thumbnail_image.delete(False) 


class ThumbnailSize(models.Model):
    """
    Represents a size configuration for thumbnails.
    """
    name = models.CharField(max_length=20, unique=True)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    def __str__(self):
        return f"Thumbnail {self.width}x{self.height}px"


class AccountTier(models.Model):
    """
    Represents an account tier with specific configurations.
    """
    name = models.CharField(max_length=20, unique=True)
    thumbnail_sizes = models.ManyToManyField(ThumbnailSize)
    link_to_original = models.BooleanField(default=False)
    generate_expiring_links = models.BooleanField(default=False)

    def __str__(self):
        thumbnail_sizes_str = ', '.join([th.name for th in self.thumbnail_sizes.all()])
        return f"{self.name} tier: {'can' if self.link_to_original else 'can`t'} LinkToOrg, {'can' if self.generate_expiring_links else 'can`t'} GenExpLink, ThumbnailSizes: {thumbnail_sizes_str}"


class GrantedTier(models.Model):
    """
    Associates an user with granted account tiers.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    granted_tiers = models.ManyToManyField(AccountTier)

    def __str__(self):
        tier_names = self.granted_tiers.values_list('name', flat=True)
        granted_tiers_str = ', '.join(tier_names)
        return f"{self.user.username}'s Granted Tiers: {granted_tiers_str}"
    

class ExpiringLink(models.Model):
    """
    Represents an expiring link associated with a base image.
    """
    base_image = models.ForeignKey(Image, on_delete=models.CASCADE)
    expiring_image = models.ImageField(upload_to='expiring/%Y/%m/%d/', max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    seconds_to_expire = models.PositiveBigIntegerField(validators=[MinValueValidator(30), MaxValueValidator(30000)])

    def __str__(self):
        return f"Expiring link of {self.base_image.name}"


@receiver(post_delete, sender=ExpiringLink)
def delete_expiring_link_image(sender, instance, **kwargs):
    """
    Signal handler to delete associated expiring link image file when an ExpiringLink instance is deleted.
    """
    instance.expiring_image.delete(False)
