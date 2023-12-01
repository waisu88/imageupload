from .models import Thumbnail, GrantedTier, Image, ExpiringLink
from celery import shared_task
from easy_thumbnails.files import get_thumbnailer


@shared_task()
def create_thumbnails(user_id):
    """
    Celery task to create thumbnails for the last uploaded image of an user based on their granted tiers.
    """
    base_image = Image.objects.filter(uploaded_by__id=user_id).last()
    user_tiers = GrantedTier.objects.filter(user__id=user_id).first()

    sizes = set()
    for tier in user_tiers.granted_tiers.all():
        sizes.update((thumbnail_size.width, thumbnail_size.height) for thumbnail_size in tier.thumbnail_sizes.all())

    for size in sizes:
        thumbnailer = get_thumbnailer(base_image.image)
        th = thumbnailer.get_thumbnail({'size': size, 'crop': True})
        thumbnail_size = f"{size[0]}x{size[1]}px"
        Thumbnail.objects.create(created_by_id=user_id, base_image=base_image, thumbnail_image=str(th), thumbnail_size=thumbnail_size)
     

@shared_task()
def delete_expiring_link(*args, **kwargs):
    """
    Celery task to delete an expiring link after a specified duration.
    """
    ExpiringLink.objects.get(id=kwargs['instance_id']).delete()
