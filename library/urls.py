from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('books', views.BookViewSet, basename='book')

# Nested note routes under /books/<book_pk>/notes/
note_list = views.NoteViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
note_detail = views.NoteViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('books/cover-search/', views.CoverSearchView.as_view(), name='cover-search'),
    path('', include(router.urls)),
    path('books/<int:book_pk>/notes/', note_list, name='book-note-list'),
    path('books/<int:book_pk>/notes/<int:pk>/', note_detail, name='book-note-detail'),
]
