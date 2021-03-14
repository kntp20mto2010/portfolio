from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator
import uuid
import os
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _


class ShopData(models.Model):
    place_id = models.TextField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not username:
            raise ValueError("Users must have an username")
        elif not email:
            raise ValueError("Users must have an email address")

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


def _getImagePath(self, filename):
    upload_to = "profile_images/"
    name = str(uuid.uuid4())
    extension = os.path.splitext(filename)[-1]
    path = upload_to + name + extension
    print(path)
    return path


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        help_text=(
            "Required.150 characters or fewer.Letters,digit and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={"unique": _("A user with that username already exists."),},
    )

    email = models.EmailField(
        _("email address"),
        help_text="この項目は必須です｡メールアドレスは公開されません｡",
        blank=False,
        unique=True,
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site"),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active."
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    profile_image = models.ImageField(upload_to=_getImagePath, default="default.jpg")

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("user")
        abstract = False

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)
