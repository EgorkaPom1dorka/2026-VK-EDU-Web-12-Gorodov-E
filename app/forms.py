from django import forms
from .models import Question
from django import forms
from app.models import Answer

class AskForm(forms.ModelForm):
    tags = forms.CharField(
        label="Теги",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control d-none',
            'id': 'real-tags-input'
        }),
        help_text="Задайте до 5 тегов, разделяя их пробелом или клавишей Enter"
    )

    class Meta:
        model = Question
        fields = ['title', 'text', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Глубокий смысл вашего вопроса...'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Подробное описание проблемы...'}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваш ответ здесь...',
                'rows': 4
            }),
        }
        labels = {
            'text': '',
        }