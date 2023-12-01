from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from .models import Image, Thumbnail, ExpiringLink, ThumbnailSize, AccountTier, GrantedTier
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


class ImagesApiTestCase(TestCase):
    """
    NOTE: For running all tests, sample image file "test.png" is required in ./test_static directory.
    """
    def setUp(self):
        """
        Setup client and users.
        """
        self.client = APIClient()
        self.user1 = User.objects.create_user(username="testuser1", password="very-strong-password")
        self.user2 = User.objects.create_user(username="testuser2", password="very-strong-password")
        """
        Setup granted tiers.
        """
        thumbnail_200px = ThumbnailSize.objects.create(id=1, name="200px", width=200, height=200)
        thumbnail_400px = ThumbnailSize.objects.create(id=2, name="400px", width=400, height=400)
        enterprise_tier = AccountTier.objects.create(id=1, name="Enterprise", link_to_original=True, generate_expiring_links=True)
        enterprise_tier.thumbnail_sizes.add(thumbnail_200px, thumbnail_400px)
        premium_tier = AccountTier.objects.create(id=2, name="Premium", link_to_original=True, generate_expiring_links=False)
        premium_tier.thumbnail_sizes.add(thumbnail_200px, thumbnail_400px)
      
        user1_granted_tiers = GrantedTier.objects.create(id=1, user=self.user1)
        user1_granted_tiers.granted_tiers.add(enterprise_tier)
        user2_granted_tiers = GrantedTier.objects.create(id=2, user=self.user2)
        user2_granted_tiers.granted_tiers.add(premium_tier)
        """
        Setup Image, Thumbnail and ExpiringLink objects.
        """
        test_image_path = 'images_api/tests_static/test.png'
        with open(test_image_path, 'rb') as image_file:
            self.image_1 = Image.objects.create(
                id=1,
                name="image1",
                image=SimpleUploadedFile("image.png", image_file.read()),
                slug='image1-1',
                uploaded_by=self.user1
            )
            self.image_2 = Image.objects.create(
                id=2,
                name="image2",
                image=SimpleUploadedFile("image.png", image_file.read()),
                slug='image2-2',
                uploaded_by=self.user2
            )

        Thumbnail.objects.create(id=1, created_by=self.user1, base_image=self.image_1, 
                                 thumbnail_image="th_img.png", thumbnail_size="200px")
        Thumbnail.objects.create(id=2, created_by=self.user1, base_image=self.image_1, 
                                 thumbnail_image="th_img.png", thumbnail_size="400px")
        ExpiringLink.objects.create(id=55, base_image=self.image_1, expiring_image="image_exp.png", seconds_to_expire=30)

    """
    TESTS

    1. Create tests.
    """
    def test_create_image(self):
        object = Image.objects.get(id=1)
        self.assertIsInstance(object, Image)

    def test_create_thumbnail(self):
        object = Thumbnail.objects.get(id=1)
        self.assertIsInstance(object, Thumbnail)
    
    def test_create_expiring_link(self):
        object = ExpiringLink.objects.get(id=55)
        self.assertIsInstance(object, ExpiringLink)

    """
    2. Authentication tests.
    """
    def test_images_list_user_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("list-create-images"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_images_list_user_un_authenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("list-create-images"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_image_detail_user_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('image-detail-destroy', kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_image_detail_user_un_authenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('image-detail-destroy', kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_cannot_access_other_user_image(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('image-detail-destroy', kwargs={'slug': "image2-2"})) # image2 created by self.user2
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_can_list_expiring_links_user_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('expiring-list-create', kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_list_expiring_links_user_un_authenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('expiring-list-create', kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_expiring_link_user_un_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('expiring-list-create', kwargs={'slug': "image1-1"})
        response = self.client.post(url, {'seconds_to_expire': 30})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_expiring_link_user_authenticated_has_permission(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('expiring-list-create', kwargs={'slug': "image1-1"})
        response = self.client.post(url, {'seconds_to_expire': 30})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_expiring_link_user_authenticated_no_permission(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('expiring-list-create', kwargs={'slug': "image2-2"})
        response = self.client.post(url, {'seconds_to_expire': 30})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 
    
    """
    3. Validation tests.
    """
    def test_create_image_bad_extension_bmp(self):
        Image.objects.create(id=5, image="img.bmp", name="bmp", slug="bmp-5", uploaded_by=self.user1)
        object = Image.objects.get(id=5)
        self.assertRaises(ValidationError, object.full_clean)
    
    def test_create_image_bad_extension_pdf(self):
        Image.objects.create(id=6, image="img.pdf", name="pdf", slug="pdf-6", uploaded_by=self.user1)
        object = Image.objects.get(id=6)
        self.assertRaises(ValidationError, object.full_clean)

    def test_create_image_bad_extension_tiff(self):
        Image.objects.create(id=7, image="img.tiff", name="tiff", slug="tiff-7", uploaded_by=self.user1)
        object = Image.objects.get(id=7)
        self.assertRaises(ValidationError, object.full_clean)

    def test_create_image_bad_extension_svg(self):
        Image.objects.create(id=8, image="img.svg", name="svg", slug="svg-8", uploaded_by=self.user1)
        object = Image.objects.get(id=8)
        self.assertRaises(ValidationError, object.full_clean)

    def test_create_expiring_link_less_than_30_seconds(self):
        ExpiringLink.objects.create(id=2, base_image=self.image_1, expiring_image="image_exp.png", seconds_to_expire=20)
        object = ExpiringLink.objects.get(id=2)
        self.assertRaises(ValidationError, object.full_clean)

    def test_create_expiring_link_more_than_30000_seconds(self):
        ExpiringLink.objects.create(id=3, base_image=self.image_1, expiring_image="image_exp.png", seconds_to_expire=30001)
        object = ExpiringLink.objects.get(id=3)
        self.assertRaises(ValidationError, object.full_clean)

    """
    4.  Destroy tests.
    """
    def test_delete_image(self): # should delete Image and Thumbnail instances associated to it by ForeignKey relation.
        self.client.force_authenticate(user=self.user1)
        count_img_before = Image.objects.count()
        count_th_before = Thumbnail.objects.count()
        response = self.client.delete(f'/images/images/{self.image_1.slug}/')
        count_img_after = Image.objects.count()
        count_th_after = Thumbnail.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(count_img_after, count_img_before - 1)
        self.assertEqual(count_th_after, count_th_before - 2)
    
    def test_nonexisting_image_deletion_returns_not_found(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete('images/images/nonexisting-slug/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    """
    5.  Invalid methods tests.
    """
    def test_invalid_method_returns_method_not_allowed_list_create_images(self):
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.put(reverse("list-create-images"))
        response2 = self.client.delete(reverse("list-create-images"))
        response3 = self.client.patch(reverse("list-create-images"))
        self.assertEqual(response1.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response2.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response3.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invalid_method_returns_method_not_allowed_image_detail_destroy(self):
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.put(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        response2 = self.client.post(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        response3 = self.client.patch(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        self.assertEqual(response1.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response2.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response3.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_invalid_method_returns_method_not_allowed_expiring_list_create(self):
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.put(reverse("expiring-list-create", kwargs={'slug': "image1-1"}))
        response2 = self.client.delete(reverse("expiring-list-create", kwargs={'slug': "image1-1"}))
        response3 = self.client.patch(reverse("expiring-list-create", kwargs={'slug': "image1-1"}))
        self.assertEqual(response1.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response2.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response3.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    """
    6.  Invalid input tests.
    """
    def test_invalid_input_when_creating_image_returns_bad_request(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse("list-create-images"), {'invalid_field': 'Invalid Value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_field_when_creating_image_returns_bad_request(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse("list-create-images"), {'name': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    """
    7.  Cache tests.
    """
    def test_cache_is_invalidated_after_image_deletion(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Delete the image and check if the cache is invalidated
        response = self.client.delete(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(reverse("image-detail-destroy", kwargs={'slug': "image1-1"}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
