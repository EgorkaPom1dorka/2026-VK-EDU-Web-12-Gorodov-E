from django.db.models import Count
from django.contrib.auth.models import User
from app.models import Tag

def sidebar_data(request):
    popular_tags = Tag.objects.annotate(
        questions_count=Count('questions')
    ).order_by('-questions_count')[:5]

    best_users = User.objects.annotate(
        answers_count=Count('answers')
    ).order_by('-answers_count')[:5]

    return {
        'popular_tags': popular_tags,
        'best_users': best_users,
    }