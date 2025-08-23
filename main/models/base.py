from django.db import models
from django.utils.text import slugify

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Slugged(models.Model):
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    class Meta:
        abstract = True

    def _slug_source(self) -> str:
        # Override in subclasses if needed
        return getattr(self, "title", "") or getattr(self, "name", "")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self._slug_source())[:200] or "item"
            candidate = base
            i = 2
            Model = self.__class__
            while Model.objects.filter(slug=candidate).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)
