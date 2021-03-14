from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from django.views.static import serve  # 追加

urlpatterns = [
    path("admin/", admin.site.urls),
    path("main/", views.main, name="main"),
    path("", include("accounts.urls")),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("search/", views.search, name="search"),
    # path("profile/", views.change_user_info, name="profile"),
    path("contact/", views.contact, name="contact"),
    path("contact_us/", views.contactUs, name="contact_us"),
    path("upload/", views.file_upload, name="upload"),
    path("ajax/", views.ajax, name="ajax"),
    path('favorite/',views.get_favorites,name='favorite'),
    path("oauth/", include("social_django.urls", namespace="social")),
    # path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

