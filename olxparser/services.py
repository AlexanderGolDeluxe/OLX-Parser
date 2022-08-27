import threading

import requests
from bs4 import BeautifulSoup
from django.conf import settings

from .models import CarsAds

LOCKER = threading.Lock()


def get_user_permissions(user_obj):
    """Возвращает данные по отображению контента
    согласно категории доступа пользователя"""
    return (
        settings.USERS_VIEW_PERMISSIONS.get(
            user_obj.username,
            settings.USERS_VIEW_PERMISSIONS.get("default")))


def threading_waiter(thr_list):
    """Останавливает выполнение кода
    до завершения отработки всех потоков в списке"""
    for thr in thr_list:
        thr.join()
    
    thr_list.clear()


def count_requested_pages(user_amount_ads):
    """Высчитывает необходимое количество запрашиваемых страниц,
    для получения определённого числа объявлений"""
    amount_pages_needed = 1
    while amount_pages_needed * settings.OLX_AMOUNT_LOADED_ADS_PER_PAGE < user_amount_ads:
        amount_pages_needed += 1
    
    return amount_pages_needed


def get_page_soup_by_url(page_url):
    """Выполняет GET запрос на страницу и
    возвращает объект для её парсинга"""
    response_page = requests.get(page_url)
    return BeautifulSoup(response_page.text, "lxml")


def get_car_seller_name_and_car_img(car_ad_data):
    """Запрашивает, после чего добавляет в данные объявления
    имя продавца и ссылку на фотографию машины"""
    soup = get_page_soup_by_url(car_ad_data.get("link_to_ad", ""))
    seller_name_tag = soup.find("h4")
    car_ad_data_to_add = dict(
        seller_name=(
            seller_name_tag.text
            if seller_name_tag else car_ad_data.get("title_ad")
        ),
        link_to_car_img=(
            (soup.find("img", {"data-testid": "swiper-image"}) or
            settings.DEFAULT_CAR_IMG).get("src")
        )
    )
    with LOCKER:
        car_ad_data.update(car_ad_data_to_add)


def updating_cars_ads(cars_ads):
    """Добавляет дополнительные данные по объявлению и
    записывает всё в базу"""
    thr_list = list()
    for car_ad_data in cars_ads:
        thr = threading.Thread(
            target=get_car_seller_name_and_car_img,
            args=(car_ad_data,)
        )
        thr_list.append(thr)
        thr.start()

    threading_waiter(thr_list)
    threading.Thread(target=save_cars_ads_to_db, args=(cars_ads,)).start()
    del thr_list


def save_cars_ads_to_db(cars_ads):
    """Записывает исключительно новые объявления в БД"""
    cars_ads_to_insert = list()
    all_ads_links = {car_ad.get("link_to_ad") for car_ad in cars_ads}
    existing_ads_links = {
        car_ad.link_to_ad
        for car_ad in CarsAds.objects.filter(link_to_ad__in=all_ads_links)
    }
    for car_ad in cars_ads:
        car_ad_obj = CarsAds(**car_ad)
        link_to_car_ad = car_ad.get("link_to_ad")
        if not link_to_car_ad in existing_ads_links:
            cars_ads_to_insert.append(car_ad_obj)
            existing_ads_links.add(link_to_car_ad)
    
    if cars_ads_to_insert:
        CarsAds.objects.bulk_create(cars_ads_to_insert)


def get_cars_ads_by_link(cars_ads, page_url):
    """Добавляет в общий список объекты объявлений для парсинга"""
    soup = get_page_soup_by_url(page_url)
    soup_cars_ads = soup.find_all("div", attrs={"data-cy": "l-card"})
    with LOCKER:
        cars_ads.extend(soup_cars_ads)


def get_cars_ads_data(cars_ads_data, car_ad_soup):
    """Парсит из объекта объявления ссылку на него в сети,
    заголовок и цену машины, а после вносит эти данные в общий список"""
    car_ad_data = dict(
        link_to_ad = settings.OLX_URL + car_ad_soup.find("a").get("href"),
        title_ad = car_ad_soup.find("h6").text,
        car_price = (
            car_ad_soup.find("p", {"data-testid": "ad-price"}).text.rstrip("Договорная").strip()
        )
    )
    with LOCKER:
        cars_ads_data.append(car_ad_data)


def get_olx_ads(request):
    """Проводит общий цикл получения информации по объявлениям со страниц,
    запись их в базу и в конце возвращает данные в виде списка со словарями"""
    cars = list()
    cars_ads = list()
    thr_list = list()
    user_view_permission = get_user_permissions(request.user)
    user_amount_requested_ads = user_view_permission.get("amount_requested_ads")
    amount_requested_pages = count_requested_pages(user_amount_requested_ads)
    for n_page in range(1, amount_requested_pages + 1):
        thr = threading.Thread(
            target=get_cars_ads_by_link,
            args=(cars_ads, settings.OLX_CATEGORY_URL + f"&page={n_page}")
        )
        thr_list.append(thr)
        thr.start()

    threading_waiter(thr_list)
    cars_ads = cars_ads[:user_amount_requested_ads]
    for car_ad in cars_ads:
        thr = threading.Thread(
            target=get_cars_ads_data,
            args=(cars, car_ad)
        )
        thr_list.append(thr)
        thr.start()

    threading_waiter(thr_list)
    cars_to_return = cars[:settings.AMOUNT_ADS_TO_SHOW]
    is_car_img_shown_for_user = user_view_permission.get("is_car_img_shown")
    is_seller_name_shown_for_user = user_view_permission.get("is_seller_name_shown")
    if any((is_car_img_shown_for_user, is_seller_name_shown_for_user)):
        thr = threading.Thread(target=updating_cars_ads, args=(cars_to_return,))
        thr.start()
        thr.join()
        threading.Thread(
            target=updating_cars_ads,
            args=(cars[settings.AMOUNT_ADS_TO_SHOW:],)
        ).start()
    else:
        threading.Thread(target=updating_cars_ads, args=(cars,)).start()
        cars_to_return = cars

    return cars_to_return


def parse_car_price_to_int(car_ad_obj):
    """Преобразовывает цену из строчного формата в целочисленный"""
    cleared_car_price = car_ad_obj.car_price.rstrip(" грн.").replace(" ", "")
    return int(cleared_car_price) if cleared_car_price.isdigit() else 0


def get_sorted_cars_ads_by_price(cars_ads_objs, is_sort_reversed):
    """Возвращает отсортированный список объявлений по цене"""
    return sorted(cars_ads_objs, key=parse_car_price_to_int, reverse=is_sort_reversed)
