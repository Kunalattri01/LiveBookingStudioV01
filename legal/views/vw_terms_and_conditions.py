from django.views import View
from django.shortcuts import render, redirect

class TermsConditionView(View):
    def get(self, request):

        context = {}
         
        return render(request, 'legal/terms-and-conditions.html', context)