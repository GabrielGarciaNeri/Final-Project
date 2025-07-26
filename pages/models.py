from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Quiz(models.Model):
    word = models.CharField(max_length=100)
    quiz_text = models.TextField()
    score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_answers = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.word