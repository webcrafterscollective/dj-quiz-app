from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Example: /quizzes/
    path('', views.quiz_list, name='quiz_list'),
    
    # Example: /quizzes/a1b2c3d4-e5f6-7890-1234-567890abcdef/
    path('<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    
    # Example: /quizzes/a1b2c3d4-e5f6-7890-1234-567890abcdef/take/
    path('<uuid:quiz_id>/take/', views.take_quiz, name='take_quiz'),

    # Example: /quizzes/submission/a1b2c3d4-e5f6-7890-1234-567890abcdef/result/
    path('submission/<uuid:submission_id>/result/', views.submission_result, name='submission_result'),
    
    # New URLs for Part 4
    # Example: /quizzes/my-history/
    path('my-history/', views.submission_history, name='submission_history'),

    # Example: /quizzes/my-history/submission/a1b2c3d4-e5f6-7890-1234-567890abcdef/
    path('my-history/submission/<uuid:submission_id>/', views.submission_detail, name='submission_detail'),
]

