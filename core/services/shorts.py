from core.services.util import process_embedding
from core.models import ShortsLike
from core.models.shorts import Shorts, ShortsComment
from django.shortcuts import get_object_or_404

class ShortsService:
    @staticmethod
    def create_shorts(shorts):
        shorts.embedding = process_embedding(shorts.title, shorts.description)
        shorts.save()
        return shorts

    @staticmethod
    def toggle_like(user, shorts_id):
        shorts = get_object_or_404(Shorts, id=shorts_id)
        like, created = ShortsLike.objects.get_or_create(user = user, shorts = shorts)

        if not created:
            like.delete()
            return False

        return True

    @staticmethod
    def create_comment(user, shorts_id, content):
        shorts = get_object_or_404(Shorts, id=shorts_id)
        comment = ShortsComment.objects.create(author=user, shorts=shorts, content=content)
        return comment

    @staticmethod
    def find_like_shorts(user):
        return user.like_shorts.all()
