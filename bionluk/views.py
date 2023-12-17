from random import shuffle

import templates
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import os
from .utils import load_data, optimize_delivery_routes, transform_routes_to_coordinates, calculate_route_length, plot_routes_on_map


def index(request):
    return render(request, 'index.html')

def powerbi(request):
    return render(request, 'powerbi.html')

def team(request):
    return render(request, 'team.html')

def howtouse(request):
    return render(request, 'howtouse.html')

def contact(request):
    return render(request, 'contact.html')

DEPOT_COORDINATES = (0, 0)

@require_http_methods(["GET", "POST"])
def optimize(request):
    map_html_file = None
    selected_day = None

    if request.method == 'POST':
        file = request.FILES['file']
        if file:
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            trucks_input = request.POST['trucks']
            try:
                trucks_list = [int(x.strip()) for x in trucks_input.split(',')]
                if len(trucks_list) != 5:
                    raise ValueError("Please enter exactly five numbers.")
            except ValueError as e:
                return HttpResponse(str(e))

            selected_day = int(request.POST['day'])

            data = load_data(os.path.join(settings.MEDIA_ROOT, filename))
            optimized_routes = optimize_delivery_routes(data, DEPOT_COORDINATES, trucks_list)
            transformed_routes = transform_routes_to_coordinates(optimized_routes, data)

            weekly_length = sum([calculate_route_length(route) for routes in transformed_routes.values() for route in routes])

            map_html_filename = f'map_day_{selected_day}.html'
            map_html_file = os.path.join(settings.STATIC_URL, map_html_filename)
            plot_routes_on_map(transformed_routes[selected_day], DEPOT_COORDINATES, selected_day, weekly_length).save(os.path.join(settings.STATIC_ROOT+"/generated_maps", map_html_filename))

    return render(request, 'optimize.html', {'map_html_file': map_html_file, 'selected_day': selected_day})