from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('like/', views.like, name='like'),
    path('question/<int:question_id>/', views.question, name='question_detail'),
    path('answer/like/', views.answer_like, name='answer_like'),
    path('answer/correct/', views.mark_correct, name='mark_correct'),
]
