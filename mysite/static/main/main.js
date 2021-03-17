// 現在地を取得
// 飲食店に絞る
// 距離でフィルター
// 絞れたら下部にリストで候補を表示
// クリックしたらDBで同じ店を直近で選んだ人のデータを取得
// 自分の行動と比較し候補をリストアップs
var map;
var current_latLng;
var markers = {};
var count = 0;
// Initialize and add the map
function initMap() {
    waitForElement()

    // The location of Uluru
    const uluru = { lat: 35.680, lng: 139.767 };
    // The map, centered at Uluru
    map = new google.maps.Map(document.getElementsByClassName("map")[0], {
        zoom: 14,
        center: uluru,
        mapTypeControl: false,
    });
    // The marker, positioned at Uluru
    const marker = new google.maps.Marker({
        position: uluru,
        map: map,
    });
    // Create the search box and link it to the UI element.
    const input = document.getElementsByClassName("nav__search-form")[0];
    input.style.display = 'block';
    input.index = 1;
    const searchBox = new google.maps.places.SearchBox(input);
    map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
    // nearSearch()

}
function search() {
    var input = document.getElementsByClassName("nav__search-input")[0]
    var place = input.value
    console.log(place)
    // 既にあるマーカーを削除
    deleteMakers();
    var geocoder = new google.maps.Geocoder();
    geocoder.geocode({
        address: place
    }, function (results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            var bounds = new google.maps.LatLngBounds();
            for (var i in results) {
                var result = results[0]
                console.log(result.name)

                if (result.geometry) {
                    // 緯度経度を取得
                    var latlng = result.geometry.location;
                    console.log(latlng)
                    // 住所を取得
                    var address = result.formatted_address;
                    // 検索結果地が含まれるように範囲を拡大
                    bounds.extend(latlng);
                    // マーカーのセット
                    setMarker(result);
                    nearSearch(result)
                }
            }
        } else if (status == google.maps.GeocoderStatus.ZERO_RESULTS) {
            alert("見つかりません");
        } else {
            console.log(status);
            alert("エラー発生");
        }
    })


}

function nearSearch(place) {
    //placesList配列を初期化
    placesList = new Array();
    if (navigator.geolocation) {
        // 現在地を取得
        navigator.geolocation.getCurrentPosition(
            function (position) {
                var mapLatLng;
                if (place === undefined || place === null) {
                    // 緯度・経度を変数に格納
                    mapLatLng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
                } else {
                    mapLatLng = place.geometry.location;
                }

                current_latLng = mapLatLng;
                // マップオプションを変数に格納
                var mapOptions = {
                    zoom: 19,          // 拡大倍率
                    center: mapLatLng,  // 緯度・経度
                    mapTypeControl: false,
                };
                // マップオブジェクト作成
                map = new google.maps.Map(
                    document.getElementsByClassName("map")[0], // マップを表示する要素
                    mapOptions         // マップオプション
                );
                //　マップにマーカーを表示する
                current_marker = new google.maps.Marker({
                    map: map,             // 対象の地図オブジェクト
                    position: mapLatLng   // 緯度・経度
                });

                var service = new google.maps.places.PlacesService(map);
                const keywords = ['cafe', 'bar', 'food']
                keywords.forEach((keyword) => {
                    service.nearbySearch(
                        {
                            location: mapLatLng,
                            // radius: 5,
                            // type: ["lunch", "cafe", 'dinner'],
                            keyword: keyword,
                            language: 'ja',
                            rankBy: google.maps.places.RankBy.DISTANCE,
                        },
                        displayResults
                    );
                })


            },
            // 取得失敗した場合
            function (error) {
                // エラーメッセージを表示
                switch (error.code) {
                    case 1: // PERMISSION_DENIED
                        alert("位置情報の利用が許可されていません");
                        break;
                    case 2: // POSITION_UNAVAILABLE
                        alert("現在位置が取得できませんでした");
                        break;
                    case 3: // TIMEOUT
                        alert("タイムアウトになりました");
                        break;
                    default:
                        alert("その他のエラー(エラーコード:" + error.code + ")");
                        break;
                }
            }
        )
    }
}
// function pin(position) {
//     var mapLatLng = new google.maps.LatLng(position.coords, latitude, position.coords.longitude)
//     // マップオプションを変数に格納
//     var mapOptions = {
//         zoom: 15,          // 拡大倍率
//         center: mapLatLng,  // 緯度・経度
//         mapTypeControl: false,
//     };
//     // マップオブジェクト作成
//     var map = new google.maps.Map(
//         document.getElementsByClassName("map")[0], // マップを表示する要素
//         mapOptions         // マップオプション
//     );
//     //　マップにマーカーを表示する
//     var marker = new google.maps.Marker({
//         map: map,             // 対象の地図オブジェクト
//         position: mapLatLng   // 緯度・経度
//     });
// }
// // 取得失敗した場合
// function fail(error) {
//     // エラーメッセージを表示
//     switch (error.code) {
//         case 1: // PERMISSION_DENIED
//             alert("位置情報の利用が許可されていません");
//             break;
//         case 2: // POSITION_UNAVAILABLE
//             alert("現在位置が取得できませんでした");
//             break;
//         case 3: // TIMEOUT
//             alert("タイムアウトになりました");
//             break;
//         default:
//             alert("その他のエラー(エラーコード:" + error.code + ")");
//             break;
//     }
// }

var placesList;
/*
 周辺検索の結果表示
 ※nearbySearchのコールバック関数
  results : 検索結果
  status ： 実行結果ステータス
  pagination : ページネーション
*/

function displayResults(results, status, pagination) {
    var infowindow = new google.maps.InfoWindow();
    if (status == google.maps.places.PlacesServiceStatus.OK) {
        //検索結果をplacesList配列に連結
        placesList = placesList.concat(results);

        //pagination.hasNextPage==trueの場合、
        //続きの検索結果あり
        if (pagination.hasNextPage) {

            //pagination.nextPageで次の検索結果を表示する
            //※連続実行すると取得に失敗するので、
            //1秒くらい間隔をおく
            setTimeout(pagination.nextPage(), 1000);

            //pagination.hasNextPage==falseになったら
            //全ての情報が取得できているので、
            //結果を表示する
        } else {

            placesList.sort(function (a, b) {

                return (haversine_distance(current_latLng, a.geometry.location) < haversine_distance(current_latLng, b.geometry.location)) ? -1 : 1;
            });
            placesList = placesList.slice(0, 20);

            //placesList配列をループして、
            //結果表示のHTMLタグを組み立てる
            for (place in placesList) {
                var marker = setMarkerWithLabel(place)
            }

            createResultHtml(placeList)
        }

    } else {
        //エラー表示
        var results = document.getElementsByClassName("results")[0];
        if (status == google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
            results.innerHTML = "検索結果が0件です。";
        } else if (status == google.maps.places.PlacesServiceStatus.ERROR) {
            results.innerHTML = "サーバ接続に失敗しました。";
        } else if (status == google.maps.places.PlacesServiceStatus.INVALID_REQUEST) {
            results.innerHTML = "リクエストが無効でした。";
        } else if (status == google.maps.places.PlacesServiceStatus.OVER_QUERY_LIMIT) {
            results.innerHTML = "リクエストの利用制限回数を超えました。";
        } else if (status == google.maps.places.PlacesServiceStatus.REQUEST_DENIED) {
            results.innerHTML = "サービスが使えない状態でした。";
        } else if (status == google.maps.places.PlacesServiceStatus.UNKNOWN_ERROR) {
            results.innerHTML = "原因不明のエラーが発生しました。";
        }

    }
}

// 距離を測
function haversine_distance(mk1, mk2) {
    var R = 3958.8; // Radius of the Earth in miles
    var rlat1 = mk1.lat() * (Math.PI / 180);
    // Convert degrees to radians
    var rlat2 = mk2.lat() * (Math.PI / 180);
    // Convert degrees to radians
    var difflat = rlat2 - rlat1; // Radian difference (latitudes)
    var difflon = (mk2.lng() - mk1.lng())
        * (Math.PI / 180); // Radian difference (longitudes)

    var d = 2 * R
        * Math.asin(Math.sqrt(Math.sin(difflat / 2) * Math.sin(difflat / 2)
            + Math.cos(rlat1) * Math.cos(rlat2)
            * Math.sin(difflon / 2) * Math.sin(difflon / 2)));
    // console.log(d)
    return d;
}

// マーカーのセットを実施する
function setMarker(place) {
    if (markers[place.place_id]) {
        marker = markers[place.place_id]
    } else {
        var iconUrl = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png';
        marker = new google.maps.Marker({
            position: place.geometry.location,
            map: map,
            icon: iconUrl
        });

        markers[place.place_id] = marker
    }

    return marker
}
function setMarkerWithLabel(place) {
    if (markers[place.place_id]) {
        marker = markers[place.place_id]
    } else {
        var marker = new MarkerWithLabel({
            position: place.geometry.location,
            clickable: true,
            draggable: true,
            map: map,
            icon: {
                url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                scaledSize: new google.maps.Size(0, 0)
            },
            labelContent: place.name, // can also be HTMLElement
            labelAnchor: new google.maps.Point(-21, 3),
            labelClass: "labels--pink", // the CSS class for the label
            labelStyle: { opacity: 1.0 },
        })
        markers[place.place_id] = marker
        setMarkerListener(marker, place)
    }
    return marker
}
function setMarkerWithLabel2(place, person_num) {
    if (person_num > 10) {
        person_num = 10;
    }
    if (markers[place.place_id]) {
        marker = markers[place.place_id]
    } else {
        var marker = new MarkerWithLabel({
            position: place.geometry.location,
            clickable: true,
            draggable: true,
            map: map,
            icon: {
                url: '/static/media/googlemap_markers/' + person_num + "_1.png",
                scaledSize: new google.maps.Size(40, 32),
                anchor: new google.maps.Point(10, 25)
            },
            labelContent: place.name, // can also be HTMLElement
            labelAnchor: new google.maps.Point(-21, 3),
            labelClass: "labels--yellow", // the CSS class for the label
            labelStyle: { opacity: 1.0 },
        })
        markers[place.place_id] = marker
        setMarkerListener(marker, place)
    }
    return marker
}

//マーカーを削除する
function deleteMakers() {
    for (place_id in markers) {
        console.log(place_id)
        marker = markers[place_id]
        if (marker != null) {
            marker.setMap(null);
        }
        marker = null;
    }
}

var dialog;
function showDialog() {
    dialog = document.getElementsByClassName("dialog")[0];
    dialog.show();
}



function waitForElement() {
    if (typeof google === "undefined") {
        setTimeout(waitForElement, 500);
        console.log('wait')
    }
    else {
        console.log('break')
    }
}

function setMarkerListener(marker, place) {
    // 開いたら画像一覧とコメントする欄があるダイアログを表示し送信したらDBへ送られる
    google.maps.event.addListener(marker, "click", function (e) {
        openDialog(place);
    });
}

function setResultListener(button, place) {
    console.log("ボタンイベントを設定します:" + place.name);
    let next = button.nextElementSibling;
    console.log('next', next);
    button.addEventListener('click', function () {
        console.log('aaaa');
        openDialog(place);
    });
}

function openDialog(place) {
    var img_element = document.getElementsByClassName("dialog__image")[0];
    if (place.photos && place.photos.length > 0) {
        img_element.src = place.photos[0].getUrl({ "maxWidth": 720, "maxHeight": 720 });
    }
    img_element.alt = '画像がありません';
    $(function () {
        // $("*[name=good_button]").val(place.place_id)
        $('.dialog').fadeIn(200).css('display', 'flex');
        $(".dialog__title").text(place.name);
        $(".dialog__input").attr("value", place.place_id);
    });
}
/**
 * 関数
 * @param {data} data - 検索結果(json)
 * {place_id:
 *      {user_id:comment,
 *      },
 * }
 */
var result;
function saveResult(data) {
    dict = {};
    // 同一のplace_idのもの
    data.forEach(elem => {
        console.log(elem);
        if (dict[elem.fields.place_id]) {
            dict[elem.fields.place_id].push(elem);
        } else {
            dict[elem.fields.place_id] = [elem]
        }
    });
    result = dict;
    console.log(result);
}


function show() {
    deleteMakers();
    showPlaces();
}
function showPlaces() {
    for (var key in result) {
        var place_id = key;
        var datas = dict[key]
        var person_num = datas.length;
        if (!place_id) {
            continue;
        }
        showPlace(place_id, person_num);
    }
}

function showPlace(place_id, person_num) {
    console.log(place_id)
    waitForElement()
    var service = new google.maps.places.PlacesService(map);
    service.getDetails({
        placeId: place_id,
        fields: ['geometry', 'name', 'photos']
    }, function (result, status) {
        console.log("結果:" + result.photos);
        console.log("店名:" + result.name + ",人数:" + person_num)
        marker = setMarkerWithLabel2(result, person_num)
        createResultHtml(result);
        let buttons = document.getElementsByClassName("result__button");
        let button = buttons.item(buttons.length - 1);
        console.log("ボタン数:" + buttons.length);
        setResultListener(button, result);
    });
}

function createResultHtml(place) {
    var src = '';
    if (place.photos && place.photos.length > 0) {
        src = place.photos[0].getUrl({ "maxWidth": 720, "maxHeight": 720 });
    }
    let resultHTML = '';
    if (count / 3 == 0) {
        let resultHTML = "<div class='result__row'></div>";
        document.getElementsByClassName("result__list")[0].insertAdjacentHTML('beforeend', resultHTML);
    }

    resultHTML += "<div class='result__elem'>";
    if (count < 3) {
        resultHTML += "<img class='result__ranking' src='/static/media/ranking" + (count + 1) + ".png'>";
    }
    resultHTML += "<button class='result__button'>";
    resultHTML += "<img class='result__image' src = '" + src + " '>";
    resultHTML += "</button>";
    resultHTML += "<div class='result__name'>" + place.name + "</div>";
    resultHTML += "</div>";
    let list = document.getElementsByClassName("result__row");
    let last = list.item(list.length - 1);
    last.insertAdjacentHTML('beforeend', resultHTML);

    count += 1;
}

function showUsers() {
    var datas = result[place_id]
    let resultHTML = '';
    for (data in datas) {
        resultHTML += "<div class='friend__li'>";
        resultHTML += "<input class='friend__input' name='user_button' value='" + data.username + "'>";
        resultHTML += "<button class='friend__button' type='submit'><img class='friend__image' src = '/static/media/profile/model1.png' ></button >";
        resultHTML += "<p class='friend__name'>" + data.username + "</p>";
        resultHTML += "</div>";
    }
    var elem = document.getElementsByClassName("friend__form")[0];
    elem.appendChild(elem);
    // return resultHTML;
}

// ダイアログを開いたらユーザーとコメントの一覧を表示する
function open(place_id) {
    var datas = result[place_id]
    var resultHTML = '';
    for (data in datas) {
        resultHTML += "<div class='dialog__friend'>";
        resultHTML += "<div class='dialog__friend-profile'>";
        resultHTML += "<button class='dialog__friend-button'>";
        resultHTML += "<img class='dialog__friend-image' src='/static/media/profile/model1.png'></button>"
        resultHTML += "<div class='dialog__friend-name'>" + data.username + "</div>"
        resultHTML += "<div class='dialog__friend-comment'>" + data.comment + "</div>"
    }

    return resultHTML;
}
// fucntion sortMarker(){
//     latMap[latMap.length] = { 'lat': lat, 'marker': marker };
//     // 緯度並び替えの実装
//     latMap.sort(function (a, b) {
//         if (a.lat < b.lat) return 1;
//         if (a.lat > b.lat) return -1;
//         return 0;
//     });
//     for (var z = 0; z < latMap.length; z++) {
//         latMap[z].marker.setZIndex(z);
//     }

// }