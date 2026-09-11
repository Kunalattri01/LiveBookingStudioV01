from django.views import View
from django.shortcuts import render, redirect

class PrivacyPolicyView(View):
    def get(self, request):

        context = {}
         
        return render(request, 'legal/privacy-policy.html', context)