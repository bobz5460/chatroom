from django.urls import path

from . import views
#    path("", views.index, name="index"),
urlpatterns = [

    path("<str:room_name>/", views.room, name="room"),
]
