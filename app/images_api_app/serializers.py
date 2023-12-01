from rest_framework import serializers
from .models import Image, Thumbnail, ExpiringLink


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Serializer for the Thumbnail model.
    """
    base_image_name = serializers.SerializerMethodField(source="get_base_image_name")
    created_by_username = serializers.SerializerMethodField(source="get_created_by_username")

    def get_base_image_name(self, thumbnail):
        return thumbnail.base_image.name
    
    def get_created_by_username(self, thumbnail):
        return thumbnail.created_by.username

    class Meta:
        model = Thumbnail
        read_only_fields = ['thumbnail_image', 'base_image_name']
        fields = ['created_by_username', 'base_image_name', 'thumbnail_image', 'thumbnail_size', 'created_at']


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Image model.
    """
    thumbnails = ThumbnailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Image
        fields = ['id', 'name', 'slug', 'uploaded_by', 'image', 'created_at', 'thumbnails']
        read_only_fields = ['uploaded_by', 'slug'] 
    
    def to_representation(self, instance):
        """
        Modify the representation of Image instances to display only the file name for user, 
        who has no permission to preview original link to the image.
        Modify the representation of Image instances to include the username of the creator in place of id.
        """
        representation = super(ImageSerializer, self).to_representation(instance)
        representation['image'] = instance.image.name.split("/")[-1]
        representation['uploaded_by'] = instance.uploaded_by.username
        return representation


class ImageLinkToOriginalSerializer(serializers.ModelSerializer):
    """
    Serializer for the Image model with additional fields for link-to-original view.
    """
    thumbnails = ThumbnailSerializer(many=True, read_only=True)

    class Meta:
        model = Image
        fields = ['id', 'name', 'slug', 'uploaded_by', 'image', 'created_at', 'thumbnails']    
        read_only_fields = ['uploaded_by', 'slug']  
    
    def to_representation(self, instance):
        """
        Modify the representation of Image instances to include the username of the creator in place of id.
        """
        representation = super(ImageLinkToOriginalSerializer, self).to_representation(instance)
        representation['uploaded_by'] = instance.uploaded_by.username
        return representation
    
class ExpiringLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for the ExpiringLink model.
    """
    class Meta:
        model = ExpiringLink
        fields = ['id', 'expiring_image', 'base_image', 'created_at', 'seconds_to_expire']
        read_only_fields = ['expiring_image', 'base_image'] 
        