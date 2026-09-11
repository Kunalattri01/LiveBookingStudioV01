from django.views import View
from django.shortcuts import render, redirect

class SupportView(View):
    def get(self, request):

        context = {}

        return render(request, 'support/support.html', context)