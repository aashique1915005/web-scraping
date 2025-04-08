from django.urls import path
from . import views

urlpatterns = [
    path('scrape/', views.scrape_website, name='scrape_website'),
]
