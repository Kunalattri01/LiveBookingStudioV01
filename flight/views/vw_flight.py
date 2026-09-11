from django.views import View
from django.shortcuts import render, redirect

class FlightView(View):
    def get(self, request):

        context = {
            
        }

        return render(request, 'flight/flights.html', context)