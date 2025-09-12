from django.shortcuts import render
from django.http import HttpResponse

def room(request, room_name):
    return render(request, "chat/index.html", {"room_name": room_name})
