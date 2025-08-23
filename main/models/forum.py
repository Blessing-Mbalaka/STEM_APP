from django.db import models
from .base import TimeStamped, Slugged
from .user import CustomUser

class ForumCategory(TimeStamped, Slugged):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=250, blank=True)

    def _slug_source(self): return self.name
    def __str__(self): return self.name

class Thread(TimeStamped, Slugged):
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name="threads")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="threads")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_locked = models.BooleanField(False)

    def _slug_source(self): return self.title

    class Meta:
        indexes = [
            models.Index(fields=["category", "created_at"]),
        ]

    def __str__(self):
        return self.title

class Post(TimeStamped):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"]),
        ]

    def __str__(self):
        return f"Post by {self.author} in {self.thread}"

class PostLike(TimeStamped):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="post_likes")

    class Meta:
        unique_together = ("post", "user")
        indexes = [
            models.Index(fields=["post", "user"]),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.post_id}"
