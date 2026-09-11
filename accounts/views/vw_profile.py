from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from accounts.models import UserProfile


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, "accounts/profile.html", {"profile": profile})

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.save(update_fields=["first_name", "last_name"])
        profile.phone = request.POST.get("phone", "").strip()
        profile.preferred_currency = request.POST.get("preferred_currency", "INR").upper()[:3]
        profile.timezone = request.POST.get("timezone", "Asia/Kolkata").strip()
        profile.save()
        return redirect("ProfilePage")
