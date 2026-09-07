from rest_framework import serializers

from .models import Book, Note


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'genre',
            'status',
            'cover_color',
            'cover_url',
            'rating',
            'page_count',
            'date_started',
            'date_finished',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('id', 'content', 'entry_type', 'created_at')
        read_only_fields = ('id', 'created_at')

