from django.db import models
from django.conf import settings

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Chat')
    
    # Simpler approach: Store messages as a JSON list
    # Format: [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    history = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        db_table = 'chat_session'

    def __str__(self):
        return f"{self.user} - {self.title}"
