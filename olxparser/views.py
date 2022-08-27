from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import View

from .decorators import unauthenticated_user
from .models import CarsAds
from .services import (get_olx_ads, get_sorted_cars_ads_by_price,
                       get_user_permissions)


class LoadCarsAds(View):
    def get(self, request):
        cars_ads = get_olx_ads(request)
        user_view_permission = get_user_permissions(request.user)
        context = dict(
            data=cars_ads,
            is_car_img_shown=user_view_permission.get("is_car_img_shown"),
            is_seller_name_shown=user_view_permission.get("is_seller_name_shown")
        )
        return JsonResponse(context, safe=False)


class DeleteAd(View):
    def get(self, request):
        link_ad_to_delete = request.GET.get("link_ad_to_delete")
        ad_obj_to_delete = CarsAds.objects.get(link_to_ad=link_ad_to_delete)
        ad_obj_to_delete.delete()
        return JsonResponse(dict(data={"deleted_obj_title": ad_obj_to_delete.title_ad}))


@login_required(login_url="login_page")
def index(request):
    showed_ads = ""
    n_page = request.GET.get("page")
    sorted_by_price = request.GET.get("sorted_by_price", "")
    user_view_permission = get_user_permissions(request.user)
    if n_page:
        cars_ads_objs = CarsAds.objects.all().order_by("-ad_created")
        if sorted_by_price:
            is_sort_reversed = sorted_by_price == "true"
            sorted_by_price = "&sorted_by_price=" + sorted_by_price
            cars_ads_objs = get_sorted_cars_ads_by_price(
                cars_ads_objs,
                is_sort_reversed)
        
        p = Paginator(cars_ads_objs, settings.AMOUNT_ADS_TO_SHOW)
        if n_page == "last":
            n_page = p.num_pages
        showed_ads = p.get_page(n_page)
    
    context = dict(
        showed_ads=showed_ads,
        sorted_by_price=sorted_by_price,
        amount_requested_ads=user_view_permission.get("amount_requested_ads"),
        is_car_img_shown=user_view_permission.get("is_car_img_shown"),
        is_seller_name_shown=user_view_permission.get("is_seller_name_shown")
    )
    return render(request, "olxparser/index.html", context)


@unauthenticated_user
def sign_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("index_page")
        else:
            messages.info(request, "Вы ввели неправильный Логин или Пароль")
    
    return render(request, "olxparser/login.html")


def sign_out(request):
    logout(request)
    return redirect("login_page")
