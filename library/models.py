from django.conf import settings
from django.db import models


class Book(models.Model):
    STATUS_CHOICES = [
        ('want_to_read', 'Want to Read'),
        ('reading', 'Reading'),
        ('read', 'Read'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='books',
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='want_to_read',
    )
    cover_color = models.CharField(max_length=7)  # hex color, e.g. #A3B18A
    cover_url = models.URLField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    date_started = models.DateField(null=True, blank=True)
    date_finished = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.author}'


class Note(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('note', 'Note'),
        ('quote', 'Quote'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    content = models.TextField()
    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPE_CHOICES,
        default='note',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        preview = self.content[:50] + ('…' if len(self.content) > 50 else '')
        return f'[{self.get_entry_type_display()}] {preview}'
