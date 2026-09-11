from django.views import View
from django.shortcuts import render, redirect

class HotelView(View):
    def get(self, request):

        context = {}
         
        return render(request, 'hotel/hotel.html', context)