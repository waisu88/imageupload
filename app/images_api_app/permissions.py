from rest_framework import permissions
from .models import GrantedTier
    
class CreateExpiringLinkPermission(permissions.BasePermission):
    """
    Custom permission to check if a user has the permission to create expiring links.
    """
    def has_permission(self, request, view):
        """
        Check if the user has the necessary tier permissions to generate expiring links.
        """
        return GrantedTier.objects.filter(user=request.user, granted_tiers__generate_expiring_links=True).exists()
      