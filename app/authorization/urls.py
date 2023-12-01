from django.urls import path
from .views import LoginAPIView, AuthAPIOverview, LogoutAPIView


urlpatterns = [
    path('', AuthAPIOverview.as_view(), name="authorization"),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
]