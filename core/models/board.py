from django.db import models
from django.conf import settings

class BoardCategory(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='게시판 카테고리 이름'
    )

    class Meta:
            verbose_name = "게시판 카테고리"
            verbose_name_plural = "게시판 카테고리 목록"

    def __str__(self):
        return self.name


class Board(models.Model):
    category = models.ForeignKey(
         BoardCategory,
         on_delete=models.SET_NULL,
         null=True,
         verbose_name='카테고리'
    )
    title = models.CharField(
         max_length=200,
         verbose_name='제목'
    )
    content = models.TextField(
         verbose_name='내용'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name='작성자',
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="생성일"
    )
    class Meta:
        verbose_name = "게시글"
        verbose_name_plural = "게시글 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

