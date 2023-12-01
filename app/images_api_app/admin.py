from django.contrib import admin
from .models import Image, Thumbnail, ThumbnailSize, AccountTier, GrantedTier, ExpiringLink
# Register your models here.

admin.site.register((Image, Thumbnail, ThumbnailSize, AccountTier, GrantedTier, ExpiringLink))