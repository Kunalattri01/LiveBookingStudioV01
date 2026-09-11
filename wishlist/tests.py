from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from .models import Wishlist, WishlistItem


class WishlistTests(TestCase):
    def test_default_wishlist_can_store_generic_item(self):
        user = get_user_model().objects.create_user(username="demo", password="pass-12345")
        wishlist = Wishlist.objects.create(user=user)
        content_type = ContentType.objects.get_for_model(Wishlist)
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            content_type=content_type,
            object_id=str(wishlist.pk),
            title="Saved item",
        )
        self.assertEqual(wishlist.items.count(), 1)
        self.assertEqual(item.title, "Saved item")
