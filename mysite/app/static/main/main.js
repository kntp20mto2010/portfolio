// 現在地を取得
// 飲食店に絞る
// 距離でフィルター
// 絞れたら下部にリストで候補を表示
// クリックしたらDBで同じ店を直近で選んだ人のデータを取得
// 自分の行動と比較し候補をリストアップs
var map;
var current_latLng;
var post_markers;
var markers;
// 1分ごとに座標を確認し､3分間十分に近かった場合そこに滞在したとみなす
//
function search() {
    var geocoder = new google.maps.Geocoder();
    geocoder.geocode({
        address: place
    }, function (results, status) {
        if (status == google.maps.GeocoderStatus.OK) {

            var bounds = new google.maps.LatLngBounds();

            for (var i in results) {
                if (results[0].geometry) {
                    // 緯度経度を取得
                    var latlng = results[0].geometry.location;
                    // 住所を取得
                    var address = results[0].formatted_address;
                    // 検索結果地が含まれるように範囲を拡大
                    bounds.extend(latlng);
                    // マーカーのセット
                    setMarker(latlng);
                    // マーカーへの吹き出しの追加
                    // setInfoW(place, latlng, address);
                    // マーカーにクリックイベントを追加
                    // markerEvent();
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

function nearSearch() {
    //placesList配列を初期化
    placesList = new Array();
    if (navigator.geolocation) {
        // 現在地を取得
        navigator.geolocation.getCurrentPosition(
            function (position) {
                // 緯度・経度を変数に格納
                var mapLatLng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
                current_latLng = mapLatLng;
                // マップオプションを変数に格納
                var mapOptions = {
                    zoom: 17,          // 拡大倍率
                    center: mapLatLng  // 緯度・経度
                };
                // マップオブジェクト作成
                map = new google.maps.Map(
                    document.getElementById("map"), // マップを表示する要素
                    mapOptions         // マップオプション
                );
                //　マップにマーカーを表示する
                current_marker = new google.maps.Marker({
                    map: map,             // 対象の地図オブジェクト
                    position: mapLatLng   // 緯度・経度
                });

                var service = new google.maps.places.PlacesService(map);
                service.nearbySearch(
                    {
                        location: mapLatLng,
                        // radius: 5,
                        // type: ["food", "cafe", 'restaurant'],
                        keyword: 'カフェ OR 居酒屋 OR 食べ物',
                        language: 'ja',
                        rankBy: google.maps.places.RankBy.DISTANCE,
                    },
                    displayResults
                );
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
function pin(position) {
    var mapLatLng = new google.maps.LatLng(position.coords, latitude, position.coords.longitude)
    // マップオプションを変数に格納
    var mapOptions = {
        zoom: 15,          // 拡大倍率
        center: mapLatLng  // 緯度・経度
    };
    // マップオブジェクト作成
    var map = new google.maps.Map(
        document.getElementById("map"), // マップを表示する要素
        mapOptions         // マップオプション
    );
    //　マップにマーカーを表示する
    var marker = new google.maps.Marker({
        map: map,             // 対象の地図オブジェクト
        position: mapLatLng   // 緯度・経度
    });
}
// 取得失敗した場合
function fail(error) {
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
            placesList = placesList.slice(0, 10);

            //placesList配列をループして、
            //結果表示のHTMLタグを組み立てる
            var resultHTML = "<ul>";

            for (var i = 0; i < placesList.length; i++) {
                place = placesList[i];
                //ratingがないのものは「---」に表示変更
                var rating = place.rating;
                if (rating == undefined) rating = "---";
                //表示内容（評価＋名称）
                resultHTML += "<li>";

                if (place.photos && place.photos.length >= 1) {
                    resultHTML += "<button class='result_button' onclick='showDialog()'><img src='" + place.photos[0].getUrl({ "maxWidth": 240, "maxHeight": 240 }) + "' class='result_image shadow size' />";
                }
                // current = id;
                // var infowindow = overlays[id][1];
                // infowindow.setContent("<div class='infowin'>" + s + "</div>");
                // if (openFLG[id] != 1) {
                //     infowindow.open(map, this);
                //     openFLG[id] = 1;
                // } else {
                //     infowindow.close();
                //     openFLG[id] = 0;
                // }
                // if ('photos' in place) {
                //     resultHTML += "<img src='https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=" + place.photos[0].photo_reference + "&key=AIzaSyCtcFEP6NzAHWBHySPAkD_E3Ua4mFx2fOY'>";
                // } else {

                // }
                resultHTML += "<p>" + place.name + "</p>";
                // resultHTML += "<p>" + place.rating + "</p>";
                resultHTML += "</button>"
                resultHTML += "</li>";

                var iconUrl = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png';
                //　マップにマーカーを表示する
                var marker = new google.maps.Marker({
                    map: map,             // 対象の地図オブジェクト
                    position: place.geometry.location,   // 緯度・経度
                    icon: {
                        url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',                      //アイコンのURL
                        scaledSize: new google.maps.Size(16, 16) //サイズ
                    },
                });
                markers[place.name] = marrker

                //マーカーにイベントリスナを設定
                marker.addListener('click', function () {
                    infowindow.setContent(place.name);  //results[i].name
                    infowindow.open(map, this);
                });
                console.log(place.name)
            }

            resultHTML += "</ul>";

            //結果表示
            document.getElementById("results").innerHTML = resultHTML;
        }

    } else {
        //エラー表示
        var results = document.getElementById("results");
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
    console.log(d)
    return d;
}

// 押したら美味しいかまずいか選ぶダイアログが出る
// それを押したら評価完了 DBへ登録し
// 似た傾向のある人を検索し表示する
function addMyList() {

}

// マーカーのセットを実施する
function setMarker(setplace) {
    // 既にあるマーカーを削除
    deleteMakers();

    var iconUrl = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png';
    marker = new google.maps.Marker({
        position: setplace,
        map: map,
        icon: iconUrl
    });
}

//マーカーを削除する
function deleteMakers() {
    if (marker != null) {
        marker.setMap(null);
    }
    marker = null;
}

// マーカーへの吹き出しの追加
function setInfoW(place, latlng, address) {
    infoWindow = new google.maps.InfoWindow({
        content: "<a href='http://www.google.com/search?q=" + place + "' target='_blank'>" + place + "</a><br><br>" + latlng + "<br><br>" + address + "<br><br><a href='http://www.google.com/search?q=" + place + "&tbm=isch' target='_blank'>画像検索 by google</a>"
    });
}

// $(function () {
//     $('.result_button').hover(
//         function () {
//             $(this).children('.tooltip').fadeIn('fast');
//         },
//         function () {
//             $(this).children('.tooltip').fadeOut('fast');
//         });
// });

var dialog;
function showDialog() {
    dialog = document.getElementById("dialog");
    dialog.show();

}

// databaseへinsertする
function submit(user, status) {

}