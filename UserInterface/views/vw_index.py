import json

from django.views import View
from django.shortcuts import render, redirect

from flight.models import Airport


class HomeView(View):
    def get(self, request):

        airports = list(
            Airport.objects.filter(is_active=True)
            .order_by('-is_popular', 'city')
            .values('code', 'city', 'airport_name')
        )

        airports_json = json.dumps([
            {'code': a['code'], 'city': a['city'], 'airport': a['airport_name']}
            for a in airports
        ])

        context = {
            'airports_json': airports_json,
        }

        return render(request, 'index.html', context)