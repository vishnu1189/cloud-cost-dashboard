from django.urls import path
from .views import home, analyse_cost_json_api

urlpatterns = [
    path('', home, name='home'),
    path('api/analyse-cost-json', analyse_cost_json_api, name='analyse_cost_json_api'),
]