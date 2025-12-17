from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    profile_image = models.CharField(
        'profile image URL',
        max_length=500,
        null=True,
        blank=True
    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username
