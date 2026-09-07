from django.contrib import admin

from .models import Book, Note


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'user', 'created_at')
    list_filter = ('status',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('content_preview', 'entry_type', 'book', 'created_at')
    list_filter = ('entry_type',)

    @admin.display(description='Content')
    def content_preview(self, obj):
        return obj.content[:80] + ('…' if len(obj.content) > 80 else '')
