from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
@login_required
def room(request, room_name):
    return render(request, "chat/index.html", {"room_name": room_name})
def login(request):
    username=request.POST['username']
    password=request.POST['password']
    user = authenticate(request, username=username, password=password)
