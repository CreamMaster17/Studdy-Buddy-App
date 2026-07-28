from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)
    pass


class UserProfile(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    nickname = models.CharField(max_length=50, blank=True, db_default="")
    
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    def __str__(self):
        return self.user.username
