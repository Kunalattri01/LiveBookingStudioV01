from django.views import View
from django.shortcuts import render, redirect

class UserAgreementView(View):
    def get(self, request):

        context = {}
         
        return render(request, 'legal/user-agreement.html', context)