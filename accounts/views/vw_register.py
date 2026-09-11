from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views import View

from accounts.models import UserProfile


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("HomePage")
        return render(request, "accounts/register.html")

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "accounts/register.html")
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html")
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "accounts/register.html")

        username = email
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user)
        except IntegrityError:
            messages.error(request, "Unable to create the account. Please try again.")
            return render(request, "accounts/register.html")

        login(request, user)
        return redirect("HomePage")
