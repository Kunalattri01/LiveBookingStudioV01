from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from wishlist.models import Wishlist


class WishlistView(LoginRequiredMixin, View):
    login_url = "LoginPage"

    def get(self, request):
        wishlist = Wishlist.objects.filter(user=request.user, is_default=True).prefetch_related("items").first()
        return render(request, "wishlist/wishlist.html", {"wishlist": wishlist})
