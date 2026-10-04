from django.shortcuts import render
from .models import StarterItem
def destination(request): return render(request,"core/destination.html",{"items":StarterItem.objects.filter(is_active=True).order_by("title")})
