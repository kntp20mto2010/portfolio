from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """ログオンフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs["placeholder"] = "メールアドレスを入力"
        self.fields['password'].widget.attrs["placeholder"] = "パスワードを入力"
