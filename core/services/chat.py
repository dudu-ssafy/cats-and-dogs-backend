from core.models.chat import ChatSession

class ChatService:
    @staticmethod
    def upsert_chat_session(user, data):
        chat_id = data.get('chat_id')
        history = data.get('history', [])

        # update
        if chat_id:
            try:
                session = ChatSession.objects.get(id=chat_id, user=user)
                session.history = history
                session.save()
                return session, False
            except ChatSession.DoesNotExist:
                pass

        # create
        session = ChatSession.objects.create(
            user=user,
            title = data.get('title', 'New Chat'),
            history=history
        )
        return session, True
