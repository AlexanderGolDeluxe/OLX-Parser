from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index_page"),
    path("login/", views.sign_in, name="login_page"),
    path("logout/", views.sign_out, name="logout"),
    path("load_cars_ads/", views.LoadCarsAds.as_view(), name="load_cars_ads"),
    path("delete_ad/", views.DeleteAd.as_view(), name="delete_ad")
]
