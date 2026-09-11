from django.views import View
from django.shortcuts import render, redirect

class RefundPolicyView(View):
    def get(self, request):

        context = {}
         
        return render(request, 'legal/refund-policy.html', context)