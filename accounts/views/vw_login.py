from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.views import View


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("HomePage")
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            account = User.objects.filter(email__iexact=email).first()
            if account:
                user = authenticate(request, username=account.username, password=password)
        if user is None:
            messages.error(request, "The email or password is not correct.")
            return render(request, "accounts/login.html", {"email": email})
        if not user.is_active:
            messages.error(request, "This account is inactive.")
            return render(request, "accounts/login.html", {"email": email})
        login(request, user)
        return redirect(request.GET.get("next") or "HomePage")
