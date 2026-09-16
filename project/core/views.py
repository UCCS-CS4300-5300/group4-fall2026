from django.shortcuts import render
from .models import StarterItem
def home(request): return render(request,"core/home.html",{"items":StarterItem.objects.filter(is_active=True).order_by("title")})
