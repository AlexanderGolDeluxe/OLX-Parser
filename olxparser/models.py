from django.db import models

# Create your models here.
class CarsAds(models.Model):
    link_to_ad = models.URLField("link_to_ad", unique=True)
    title_ad = models.TextField("title_ad", max_length=500)
    seller_name = models.CharField("seller_name", max_length=100, blank=True)
    car_price = models.CharField("car_price", max_length=50, blank=True)
    link_to_car_img = models.URLField("link_to_car_img", blank=True)
    ad_created = models.DateTimeField("ad_created", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Объявление о продаже автомобиля"
        verbose_name_plural = "Объявления о продажах автомобилей"
    
    def __str__(self):
        return self.title_ad
