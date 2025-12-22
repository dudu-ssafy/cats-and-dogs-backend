from django.db import models
from django.conf import settings
from pgvector.django import VectorField


class Shorts(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='제목',
        null=True,
        blank=True,
    )
    description = models.TextField(
        '설명',
        null=True,
        blank=True
    )
    thumbnail_url = models.URLField(
        verbose_name='썸네일 URL',
        null=True,
        blank=True,
    )
    video_url = models.URLField(
        verbose_name='비디오 URL',
        null=True,
        blank=True,
    )
    embedding = VectorField(
        dimensions=1536,
        help_text='OpenAI embedding vector',
        null=True,
        blank=True
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
        return self.title if self.title else '제목 없음'



class ShortsComment(models.Model):
    shorts = models.ForeignKey(
        Shorts,
        on_delete=models.CASCADE,
        verbose_name='쇼츠',
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='작성자',
    )
    content = models.TextField(
        '내용'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일"
    )

    class Meta:
        verbose_name = "쇼츠 댓글"
        verbose_name_plural = "쇼츠 댓글 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.content
