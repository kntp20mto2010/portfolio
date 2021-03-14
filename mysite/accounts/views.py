from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import FormView
from .forms import LoginForm
from app.forms import UserChangeForm
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from app.models import User


class Login(LoginView):
    """ログインページ"""

    form_class = LoginForm
    # templates/accoutns/login.html
    template_name = "accounts/login.html"


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""

    template_name = "accounts/login.html"


class UserChangeView(LoginRequiredMixin, FormView):
    template_name = "accounts/profile.html"
    form_class = UserChangeForm
    success_url = reverse_lazy("accounts:profile")

    # unique制約のあるフィールドが存在する場合インスタンスを引数に割り当てる必要がある
    # https://yuki.world/django-modelform-update-pitfall/
    # https://e-tec-memo.herokuapp.com/article/285/
    # ProcessFormView
    def post(self, request, *args, **kwargs):
        context = {}
        obj = get_object_or_404(User, email=request.user.email)
        if request.method == "POST":
            # form.is_valid()がfalseになる
            # →UserChangeFormのinit関数は第一引数がselfであるため引数名を指定する必要がある
            # この場合はdata=Resuest.POST
            # unique制約のフィールドがあるモデルを更新する場合はinit関数にinstanceを渡す必要がある
            # 渡さなければ新規と見なされ重複チェックで弾かれる
            # フォームのインスタンスを独自に作成したためget_form()が呼ばれず､super().get_form_kwargs()も呼ばれない｡
            # そのため､自分で呼び出しUserChangeFormに与える必要がある
            # UserChangeForm(data=Request.POST,instance=obj,kwargs=kwargs)
            # としたが､UserChangeFormの引数を参照すれば分かるがdataもinstanceもkwargsとして渡されるため一つにまとめる必要がある
            # よって下記のようにまとめて渡すことになった
            kwargs = self.get_form_kwargs()
            kwargs.update({"data": request.POST, "instance": obj})
            form = UserChangeForm(**kwargs)
            if form.is_valid():
                form.save(obj)
                return render(request, "accounts/profile.html",{"form":form})
        else:
            form = UserChangeForm(instance=obj)
            context.update({"form": form})
            return render(request, "accounts/profile.html", context)

    def form_valid(self, form):
        # formのupdateメソッドにログインユーザーを渡して更新
        form.update(user=self.request.user)
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        # form_class = self.get_form_class()
        # print(form_class)
        form = self.get_form()
        kwargs = self.get_form_kwargs()
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)

    # def post(self, request, *args, **kwargs):
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)
    #     if form.is_valid():
    #         return self.form_valid(form, **kwargs)
    #     else:
    #         return self.form_invalid(form, **kwargs)

    def form_invalid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = form
        # here you can add things like:
        context["show_results"] = False
        return self.render_to_response(context)

    # def form_valid(self, form, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     context["form"] = form
    #     # here you can add things like:
    #     context["show_results"] = True
    #     return self.render_to_response(context)

    def get_form(self):
        obj = get_object_or_404(User, email=self.request.user.email)
        form = UserChangeForm(self.request.POST, instance=obj)
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 更新前のユーザー情報をkwargsとして渡す
        # kwargs.update({"email": self.request.user.email})
        # kwargs.update({"profile_image": self.request.user.profile_image})

        return kwargs

