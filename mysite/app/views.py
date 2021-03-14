from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail
from django.views.generic.edit import CreateView
from app.forms import SignUpForm
from app.forms import UploadFileForm
from app.models import ShopData
from app.models import User
from app.forms import UserChangeForm

# from django.contrib.auth.models import User


import collections
import json


# import mysite.urls
# Create your views here.
def main(request):
    user = request.user
    datas = ShopData.objects.filter(user_id=user.id)
    datas = [data.place_id for data in datas]
    if datas:
        pass
    else:
        datas = [ShopData(place_id="111", user_id="222")]
    return render(request, "main.html", {})


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        # 入力チェック
        if form.is_valid():
            form.save()
            return redirect("main")
    else:
        form = SignUpForm()

    context = {"form": form}
    return render(request, "signup.html", context)


class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "signup.html"
    success_url = reverse_lazy("main")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        self.object = user
        return HttpResponseRedirect(self.get_success_url())

def contact(request):
    return render(request, "contact.html", {})

def contactUs(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST["email"]
        re_email = request.POST["re-email"]
        contents = request.POST["contents"]
        error = ""
        if name == "":
            error += "エラー! 名前が入力されていません｡\n"
        elif email == "":
            error += "エラー! メールアドレスを入力してください\n"
        elif email != re_email:
            error += "エラー! メールアドレスが一致しません｡\n"
        elif contents == "":
            error += "エラー! お問い合わせ内容が入力されていません｡\n"

        if error == "":
            body = f"""
{name} 様､いつもFoodgramをご利用いただきありがとうございます｡
お問い合わせ内容により､返信にはお時間を頂く場合もありますがご了承ください｡
–––––––––––––––––––––––––––––––––––––––––
以下の内容でお問い合わせを受け付けました｡
–––––––––––––––––––––––––––––––––––––––––
タイトル:{request.POST['kind']}
お問い合わせ内容:

{contents}
        """
            # 相手のemailアドレスに問い合わせが完了したことを通知する
            send_mail(
                "お問い合わせ完了のお知らせ",
                body,
                "babababeriru2010@gmail.com",
                [email],
                fail_silently=False,
            )
            return HttpResponse(reverse("main"))

        else:
            return HttpResponse(error)


# goodボタンを押したらmysqlでおすすめを検索したい
@login_required
def search(request):
    user = request.user
    if request.method == "POST":
        # お店固有のIDを取得
        comment = request.POST["comment"]
        place_id = request.POST["good"]
        print(f"ユーザーID={user.id},店ID={place_id},コメント={comment}")
        data = ShopData(place_id=place_id, user_id=user.id, comment=comment)
        # なかったら追加
        data.save()
        # このお店に行った人の中で同じ傾向の人たちを探して統計を取りオススメ店をピックアップ
        result = searchRecommend(user.id, place_id)
        json_obj = json.dumps(result, indent=4)
        print(json_obj)
        print(f"候補が{len(result)}店見つかりました")
        return HttpResponse(json_obj)
    else:
        result = ["111"]
        return render(request, "main.html", {"results": result})


# 同じ店に行った人を探す
# その人達が行ったお店を多い順に並べる
# ランキング3位までを表示する
def searchRecommend(user_id, place_id):
    datas = ShopData.objects.filter(place_id=place_id)
    place_id_list = []
    for data in datas:
        if data.user_id == user_id:
            continue
        else:
            pass
        shops = ShopData.objects.filter(user_id=data.user_id)
        temp_list = [shop.place_id for shop in shops]
        if place_id_list:
            place_id_list.extend(temp_list)
        else:
            place_id_list = temp_list
    result = collections.Counter(place_id_list)
    return dict(result.most_common()[:10])

# 自分の直近3店に行った人の中で一致率の高い人をランダムで表示する
def getRecommendPersons(user1_id):
    user1_shops = ShopData.objects.filter(user_id=user_1id)[:3]
    for data in user1_shops:
        # その店に直近で1000人行ってる人のリスト
        userX_datas = (
            ShopData.objects.filter(place_id=data.place_id)
            .order_by("date")
            .reverse()[:1000]
        )
        place_id_list = []
        for user_data in userX_datas:
            if user_data.user_id == user1_id:
                continue
            else:
                pass
            shops = ShopData.objects.filter(user_id=user_data.user_id)

            temp_list = [shop.place_id for shop in shops]
            if place_id_list:
                place_id_list.extend(temp_list)
            else:
                place_id_list = temp_list
        result = collections.Counter(place_id_list)
    return dict(result.most_common()[:10])

def get_favorites(request):
    user = request.user
    dict_ = {}
    print('favorite')
    if request.method == "POST":
        print(request.POST)
        user_id = request.POST['user_button']
        json_obj = get_shops(user_id=user_id)
        return HttpResponse(json_obj,content_type='text/json-comment-filterd')
    else:
        return HttpResponse(status=401)

# 店舗の情報
# 店ID､ユーザーID､コメント
def get_shops(place_id=None, user_id=None):
    if place_id:
        datas = ShopData.objects.filter(place_id=place_id)
    elif user_id:
        datas = ShopData.objects.filter(user_id=user_id)

    json_obj = serializers.serialize('json', datas)

    # dict_={}
    # for data in datas:
    #     dict_.setdefault(data.place_id,{})
    #     dict_[data.place_id].setdefault(data.user, data.comment)

    # json_obj=json.dumps(dict_)
    return json_obj


def profile(request):
    user = request.user
    print(user)
    user_data = User.objects.filter(id=user.id)[0]
    print(user_data)
    print(user_data.profile_image)
    return render(request, "profile.html", {"user_data": user_data})


def ajax(request):
    text = request.POST.get("search")
    hoge = "Ajax Response: " + text

    return HttpResponse(hoge)


def file_upload(request):
    if request.method == "POST":
        print(f"fileupload:{request.FILES}")
        form = UploadFileForm(request.POST, request.FILES)
        print(form)
        if form.is_valid():
            data = User.objects.filter(id=request.user.id)[0]
            data.profile_image = form.cleaned_data["file"]
            data.save()
            print(data.profile_image)
            print("success")
            json_obj = json.dumps({"image":str(data.profile_image)}, indent=4)
            return HttpResponse(json_obj)
    else:
        form = UploadFileForm()
    print("fial")
    return HttpResponse("画像のアップロードに失敗しました")
