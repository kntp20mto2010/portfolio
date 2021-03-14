from django.contrib.auth.forms import AuthenticationForm

# from django.contrib.auth.models import User
from app.models import User
from django import forms
from django.forms import ModelForm
from django.core.files.storage import default_storage
from PIL import Image
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254, help_text="必須 有効なメールアドレスを入力してください。", label="Eメールアドレス"
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_texts = {
            "email": "メールアドレスを入力",
            "username": "ユーザー名を入力",
            "password1": "パスワードを入力",
            "password2": "パスワードを再入力",
        }

        for key, value in help_texts.items():
            self.fields[key].widget.attrs["placeholder"] = value


class UserChangeForm(ModelForm):
    #  プロフィール画像はファイルが選択された瞬間即アップロードするためフォーム外で実装
    profile_image = None

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {"username": "ユーザー名", "email": "メールアドレス"}
        help_texts = {
            "username": "ユーザー名を入力",
            "email": "メールアドレスを入力",
        }

    def __init__(self, email=None, *args, **kwargs):
        print("ini")
        # pop()でkargsから外しエラーを防ぐ
        # self.profile_image = kwargs.pop("profile_image")
        self.profile_image = kwargs.get('instance').profile_image

        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # ユーザーの更新前情報をフォームに挿入
        print("init")
        # if email:
        #     self.fields["email"].widget.attrs["value"] = email

        self.fields['email'].widget.attrs['class']='profile__input'
        self.fields["email"].widget.attrs["placeholder"] = "メールアドレスを入力してください"
        self.fields['username'].widget.attrs['class']='profile__input'
        self.fields["username"].widget.attrs["placeholder"] = "ユーザー名を入力してください"

    def save(self, user):
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["username"]
        print(f"セーブしました:{user.username}")
        user.save()


class UploadFileForm(forms.Form):
    file = forms.ImageField(required=True)

    def save(self):
        upload_file = self.cleaned_data['file']
        file_name = default_storage.save(upload_file.name, upload_file)
        return default_storage.url(file_name)
