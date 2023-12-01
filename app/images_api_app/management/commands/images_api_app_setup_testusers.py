from django.contrib.auth.models import User
from images_api_app.models import AccountTier, GrantedTier, ThumbnailSize
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """
    Django management command to create users, tiers, and associated objects.
    """

    def handle(self, *args, **kwargs):
        """
        Handle the command execution.

        This method creates or retrieves users, tiers, and associated objects.
        """
        self.stdout.write('Creating users.....')
        # Create or retrieve test users
        try:
            testuser1 = User.objects.get(username="testuser1")
            self.stdout.write(self.style.SUCCESS('User "testuser1" already exists.'))
        except User.DoesNotExist:
            testuser1 = User.objects.create_user(username="testuser1", password="password")
            self.stdout.write(self.style.SUCCESS('User "testuser1" created successfully.'))
        try:
            testuser2 = User.objects.get(username="testuser2")
            self.stdout.write(self.style.SUCCESS('User "testuser2" already exists.'))
        except User.DoesNotExist:
            testuser2 = User.objects.create_user(username="testuser2", password="password")
            self.stdout.write(self.style.SUCCESS('User "testuser2" created successfully.'))
        try:
            testuser3 = User.objects.get(username="testuser3")
            self.stdout.write(self.style.SUCCESS('User "testuser3" already exists.'))
        except User.DoesNotExist:
            testuser3 = User.objects.create_user(username="testuser3", password="password")
            self.stdout.write(self.style.SUCCESS('User "testuser3" created successfully.'))
        
        self.stdout.write('Creating tiers.....')
        # Create or retrieve account tiers
        tier1, created_tier1 = AccountTier.objects.get_or_create(name="Basic", defaults={'link_to_original': False, 'generate_expiring_links': False})
        tier2, created_tier2 = AccountTier.objects.get_or_create(name="Premium", defaults={'link_to_original': True, 'generate_expiring_links': False})
        tier3, created_tier3 = AccountTier.objects.get_or_create(name="Enterprise", defaults={'link_to_original': True, 'generate_expiring_links': True})

        # Create or retrieve thumbnail sizes
        thsize200, _ = ThumbnailSize.objects.get_or_create(name="200px", defaults={'width': 200, 'height': 200})
        thsize400, _ = ThumbnailSize.objects.get_or_create(name="400px", defaults={'width': 400, 'height': 400})

        # Associate thumbnail sizes with tiers if tiers were newly created
        if created_tier1:
            tier1.thumbnail_sizes.add(thsize200)
        if created_tier2:
            tier2.thumbnail_sizes.add(thsize200, thsize400)
        if created_tier3:
            tier3.thumbnail_sizes.add(thsize200, thsize400)

        # Create or retrieve GrantedTier objects and associate them with users
        testuser1_granted_tiers, created1_granted_tiers = GrantedTier.objects.get_or_create(user=testuser1)
        testuser2_granted_tiers, created2_granted_tiers = GrantedTier.objects.get_or_create(user=testuser2)
        testuser3_granted_tiers, created3_granted_tiers = GrantedTier.objects.get_or_create(user=testuser3)

        self.stdout.write('Associating tiers.....')
        # Associate tiers with GrantedTier objects if GrantedTier objects were newly created
        if created1_granted_tiers:
            testuser1_granted_tiers.granted_tiers.add(tier1)

        if created2_granted_tiers:
            testuser2_granted_tiers.granted_tiers.add(tier2)

        if created3_granted_tiers:
            testuser3_granted_tiers.granted_tiers.add(tier3)
        
        self.stdout.write('Testusers succesfully set up!')
            