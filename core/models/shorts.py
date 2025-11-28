from django.db import models
from django.conf import settings


class Shorts(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='제목'
    )
    video_url = models.URLField(
        verbose_name='비디오 URL'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='작성자',
    )
    like_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ShortsLike',
        related_name='like_shorts'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일"
    )

    class Meta:
        verbose_name = "쇼츠"
        verbose_name_plural = "쇼츠 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
