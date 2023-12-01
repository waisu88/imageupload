from django.urls import path
from .views import ImageListCreateAPIView, ImageDetailDestroyAPIView, ExpiringLinkListCreateAPIView, ImagesApiOverview

urlpatterns = [
    path('', ImagesApiOverview.as_view(), name='images-api-overview'),
    path('images', ImageListCreateAPIView.as_view(), name='list-create-images'),
    path('images/<slug:slug>/expiring/', ExpiringLinkListCreateAPIView.as_view(), name='expiring-list-create'),
    path('images/<slug:slug>/', ImageDetailDestroyAPIView.as_view(), name='image-detail-destroy'),
]
