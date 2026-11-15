from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('book-lesson/', views.book_lesson_view, name='book_lesson'),
    path('available-slots/', views.available_slots_api_view, name='available_slots_api'),
    path('lessons/<int:pk>/cancel/', views.cancel_lesson_view, name='cancel_lesson'),
    path('lessons/<int:pk>/complete/', views.complete_lesson_view, name='complete_lesson'),
    path('instructor/schedule/', views.instructor_schedule_view, name='instructor_schedule'),
    path('payment/', views.payment_view, name='payment'),
    path('content/', views.course_content_view, name='course_content'),
]
