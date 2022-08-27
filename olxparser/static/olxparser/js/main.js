const adsBox = document.querySelector(".js-ads-box");
const spinnerBox = document.getElementById("spinner_box");
const adsPaginator = document.getElementById("ads_paginator");
const selectSortParam = document.getElementById("select_sort_param");
const urlParams = new URLSearchParams(window.location.search);


if (!adsBox.childElementCount) {
    selectSortParam.hidden = true;
}
else if (urlParams.has("sorted_by_price")) {
    if (urlParams.get("sorted_by_price") == "true") {
        document.getElementById("max_to_lower_ads_sort").selected = true;
    }
    else {
        document.getElementById("lower_to_max_ads_sort").selected = true;
    }
}


function loadCarsAds() {
    const djangoPaginator = document.getElementById("django_paginator");
    spinnerBox.classList.remove("d-none");
    $.ajax({
        type: "GET",
        url: "/load_cars_ads/",
        success: function(response) {
            const data = response.data
            const is_car_img_shown = response.is_car_img_shown
            const is_seller_name_shown = response.is_seller_name_shown
            adsBox.innerHTML = ""
            spinnerBox.classList.add("d-none")
            if (selectSortParam.hidden) selectSortParam.hidden = false
            if (!djangoPaginator) adsPaginator.classList.remove("d-none")
            data.map(post=>{
                let imgTagHTML = ""
                let h3TagHTML = ""
                if (is_seller_name_shown) {
                    h3TagHTML = `<h3 class="lead">${post.seller_name}</h3>`
                }
                if (is_car_img_shown) {
                    imgTagHTML = `<img class="bd-placeholder-img card-img-top" src="${post.link_to_car_img}"
                                    width="348" height="225" style="object-fit: cover">`
                }
                adsBox.innerHTML += (
                    `<div class="col-md-4">
                        <div class="card mb-4 shadow-sm">
                            ${imgTagHTML}
                            <div class="card-body">
                                ${h3TagHTML}
                                <p class="card-text">${post.title_ad}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <a class="btn btn-sm mr-2 btn-outline-primary" href="${post.link_to_ad}" target="_blank">Перейти</a>
                                        <button class="btn btn-sm btn-outline-danger" type="button" onclick="deleteAd(this)">Удалить</button>
                                    </div>
                                    <small class="text-muted">${post.car_price}</small>
                                </div>
                            </div>
                        </div>
                    </div>`
                )
            })
            
        },
        error: function(error) {
            console.log(error)
            spinnerBox.classList.add("d-none")
        }
    })
}


function deleteAd(element) {
    const linkAdToDelete = element.previousElementSibling.href;
    const titleAdToDelete = element.parentElement.parentElement.previousElementSibling.textContent;
    const cardToRemove = element.parentElement.parentElement.parentElement.parentElement.parentElement;
    bootbox.confirm({
        message: `Вы действительно хотите удалить объявление «${titleAdToDelete}»?`,
        locale: "ru",
        callback: function(result) { 
            if (result) {
                $.ajax({
                    type: "GET",
                    url: "/delete_ad/",
                    data: {"link_ad_to_delete": linkAdToDelete},
                    success: function(response) {
                        const data = response.data
                        cardToRemove.remove()
                        bootbox.alert(`Объявление «${data.deleted_obj_title}» успешно удалено.`)
                    },
                    error: function(error) {
                        console.log(error)
                    }
                })
            } 
        }
    });
}


function getAdsOrderedByPrice(sotredParam) {
    urlParams.set("sorted_by_price", sotredParam == "max_to_lower");
    if (!urlParams.has("page")) urlParams.set("page", 1);
    window.location.href = window.location.origin + window.location.pathname + "?" + urlParams.toString();
}
