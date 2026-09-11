from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("HomePage")

    def get(self, request):
        logout(request)
        return redirect("HomePage")
