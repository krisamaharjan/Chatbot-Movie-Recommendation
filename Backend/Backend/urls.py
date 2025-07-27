from django.contrib import admin
from django.urls import path
from Chatbot.views import recommend_movies

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recommend/',recommend_movies, name='recommend'),
]
