from django.db import models
from django.conf import settings

from .user import User
from .board import Board
from .shorts import Shorts


class BoardLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'board'],
                name='unique_board_like'
            )
        ]


class ShortsLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    shorts = models.ForeignKey(
        Shorts,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'shorts'],
                name='unique_shorts_like'
            )
        ]
