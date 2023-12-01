from rest_framework import generics, permissions
from .permissions import CreateExpiringLinkPermission
from .models import Image, GrantedTier, ExpiringLink
from .serializers import ImageSerializer, ImageLinkToOriginalSerializer, ExpiringLinkSerializer
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
from .tasks import create_thumbnails, delete_expiring_link
from django.core.files.base import ContentFile
from django.http import Http404
from django.urls import reverse
from rest_framework.views import APIView


class ImagesApiOverview(APIView):
    """
    Provides an overview of image-related routes.

    Routes:
    - 'For LOGIN visit -->': Authentication endpoint.
    - 'List-Create images': List and create images.
    - 'Image detail': View details of a specific image (use its slug).
    - 'Expiring link': Generate an expiring link for a specific image.
    """

    def get(self, request):
        routes = {
            "For LOGIN visit -->": request.build_absolute_uri(reverse(('authorization'))),
            "List-Create images": request.build_absolute_uri(reverse(('list-create-images'))),
            "Image detail": request.build_absolute_uri(reverse(('list-create-images'))) + "/<slug:slug>",
            "Expiring link": request.build_absolute_uri(reverse(('list-create-images'))) + "/<slug:slug>/expiring",
            "Review Code": "https://github.com/waisu88/docker_compose_production/tree/main/app/images_api"
        }
        return Response(routes)


class ImageListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating images.

    - For listing, it returns images uploaded by the authenticated user.
    - For creation, it allows the user to upload an image and automatically generates thumbnails using Celery task.

    Optionally, if the user has the 'Link to Original' permission, the API returns additional information.
    """
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self, *args, **kwargs):
        """
        Get the queryset of images uploaded by the authenticated user.
        """
        queryset = Image.objects.filter(uploaded_by=self.request.user).select_related('uploaded_by').prefetch_related('thumbnails__created_by')
        return queryset
    
    def get_serializer_class(self): 
        """
        Determine the serializer class based on the user's granted tiers.
        If the user has the 'Link to Original' permission, use the ImageLinkToOriginalSerializer.
        """
        granted_tiers = (
            GrantedTier.objects
            .filter(user=self.request.user, granted_tiers__link_to_original=True))
        if granted_tiers:
            return ImageLinkToOriginalSerializer
        return super().get_serializer_class() 
        
    def perform_create(self, image_serializer):
        """
        Perform image creation and generate thumbnails in the background using Celery tasks.
        """
        if image_serializer.is_valid():
            user = self.request.user
            image_instance = image_serializer.save(uploaded_by=user)
            slug_str = f"{image_serializer.validated_data['name'].lower()}-{image_instance.id}"
            image_instance.slug = slug_str
            image_instance.save()
            create_thumbnails.delay(user.id)        
            return Response(image_serializer.data, status=status.HTTP_201_CREATED)
        return Response(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ImageDetailDestroyAPIView(generics.RetrieveDestroyAPIView):
    """
    API view for retrieving and deleting images.

    - For retrieval, it returns detailed information about a specific image.
    - For deletion, it removes the image and its associated thumbnails.

    Optionally, if the user has the 'Link to Original' permission, the API returns additional information.
    """

    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self, *args, **kwargs):
        """
        Get the queryset of images uploaded by the authenticated user.
        """
        queryset = Image.objects.filter(uploaded_by=self.request.user).select_related('uploaded_by').prefetch_related('thumbnails')
        return queryset
    
    def get_serializer_class(self): 
        """
        Determine the serializer class based on the user's granted tiers.
        If the user has the 'Link to Original' permission, use the ImageLinkToOriginalSerializer.
        """
        granted_tiers = (
            GrantedTier.objects.filter(user=self.request.user, granted_tiers__link_to_original=True))
        if granted_tiers:
            return ImageLinkToOriginalSerializer
        return super().get_serializer_class() 

    def retrieve(self, *args, **kwargs):
        """
        Retrieve detailed information about a specific image, caching the result for optimization.
        """
        image_slug = kwargs.get('slug')
        cache_key = f"image_detail_{image_slug}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response({'data': cached_data})

        image_instance = self.get_object()
        serializer = self.get_serializer(image_instance)
        image_details = serializer.data
        cache.set(cache_key, image_details)
        return Response({'data': image_details})
        
    def perform_destroy(self, instance):
        """
        Perform image deletion, remove associated cache, and use signals to delete associated thumbnails.
        """
        try: 
            image_slug = instance.slug
            instance.delete()
            cache_key_image = f"image_detail_{image_slug}"
            cache.delete(cache_key_image) 
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ExpiringLinkListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating expiring links associated with a specific image.

    - For listing, it returns expiring links for images uploaded by the authenticated user.
    - For creation, it allows the user to generate expiring links for a specific image.

    Requires the 'Create Expiring Link' permission.
    """
    serializer_class = ExpiringLinkSerializer
    permission_classes = [permissions.IsAuthenticated, CreateExpiringLinkPermission]

    def get_queryset(self, *args, **kwargs):
        """
        Get the queryset of expiring links associated with images uploaded by the authenticated user.
        """
        image_slug = self.kwargs['slug']
        queryset = ExpiringLink.objects.filter(
            base_image__uploaded_by=self.request.user,
            base_image__slug=image_slug,
            expiring_image__isnull=False
            )
        return queryset

    def perform_create(self, expiring_link_serializer, *args, **kwargs):
        """
        Perform expiring link creation and schedule Celery task for expiring link deletion.
        """
        image_slug = self.kwargs['slug']
        try:
            base_image = Image.objects.get(slug=image_slug)
        except Image.DoesNotExist:
            return Response({'detail': 'Base image not found.'}, status=status.HTTP_404_NOT_FOUND)

        if expiring_link_serializer.is_valid():
            picture_copy = ContentFile(base_image.image.read())
            new_picture_name = base_image.image.name.split("/")[-1]
            expiring_link_instance = expiring_link_serializer.save(base_image=base_image)
            expiring_link_instance.expiring_image.save(new_picture_name, picture_copy)
            delete_expiring_link.apply_async(
                args=[], 
                kwargs={'instance_id': expiring_link_instance.id}, 
                countdown=expiring_link_instance.seconds_to_expire
                )
            return Response(expiring_link_serializer.data, status=status.HTTP_201_CREATED)
        return Response(expiring_link_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
