import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Subquery, OuterRef
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.forms import AskForm
from app.models import Tag
from .utils import paginate
from .forms import AskForm, AnswerForm
from app.models import Question, QuestionLike, Answer, AnswerLike

logger = logging.getLogger(__name__)


def index(request):
    questions_list = Question.objects.new()

    if request.user.is_authenticated:
        # Получаем значение value голоса текущего пользователя для каждой карточки
        user_vote_subquery = QuestionLike.objects.filter(
            question=OuterRef('pk'),
            user=request.user
        ).values('value')[:1]

        questions_list = questions_list.annotate(user_vote=Subquery(user_vote_subquery))

    page_obj = paginate(questions_list, request, per_page=20)
    return render(request, 'app/index.html', {'questions': page_obj})

def hot(request):
    # Вместо жесткой фильтрации просто сортируем абсолютно ВСЕ вопросы
    # по убыванию рейтинга (от большего к меньшему)
    questions_list = Question.objects.all().order_by('-rating', '-created_at')

    # Оживляем подсветку лайков для авторизованных пользователей, как на главной
    if request.user.is_authenticated:
        user_vote_subquery = QuestionLike.objects.filter(
            question=OuterRef('pk'),
            user=request.user
        ).values('value')[:1]
        questions_list = questions_list.annotate(user_vote=Subquery(user_vote_subquery))

    # Пропускаем через пагинатор (по 20 вопросов)
    page_obj = paginate(questions_list, request, per_page=20)

    context = {
        'questions': page_obj
    }
    return render(request, 'app/hot.html', context)

def tag(request, tag_name):
    # Фильтруем вопросы, у которых есть тег с указанным именем
    # Предполагаем, что связь в модели Question называется tags (или через related_name)
    questions_list = Question.objects.filter(tags__name=tag_name).order_by('-created_at')

    # Оживляем подсветку лайков для авторизованных пользователей, как на главной
    if request.user.is_authenticated:
        user_vote_subquery = QuestionLike.objects.filter(
            question=OuterRef('pk'),
            user=request.user
        ).values('value')[:1]
        questions_list = questions_list.annotate(user_vote=Subquery(user_vote_subquery))

    # Пагинация: выводим по 20 вопросов на страницу, как и на главной
    page_obj = paginate(questions_list, request, per_page=20)

    context = {
        'tag_name': tag_name,
        'questions': page_obj  # Передаем пагинированный список
    }
    return render(request, 'app/tag.html', context)


def question(request, question_id):
    # 1. Получаем сам вопрос
    question_item = get_object_or_404(Question, id=question_id)

    # 2. Обрабатываем добавление нового ответа (POST-запрос)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question_item
            answer.author = request.user
            answer.save()
            # Редирект к свежему ответу с якорем
            return redirect(f'/question/{question_item.id}/#answer-{answer.id}')
    else:
        # Если запрос GET — создаем пустую форму
        form = AnswerForm()

    # 3. Собираем все ответы к вопросу
    answers_list = question_item.answers.all().order_by('-created_at')

    if request.user.is_authenticated:
        # Аннотируем каждый ОТВЕТ голосом текущего пользователя
        answer_vote_subquery = AnswerLike.objects.filter(
            answer=OuterRef('pk'),
            user=request.user
        ).values('value')[:1]
        answers_list = answers_list.annotate(user_vote=Subquery(answer_vote_subquery))

        # Корректно аннотируем сам ВОПРОС, чтобы в шаблоне question.html кнопки горели активным цветом
        question_vote = QuestionLike.objects.filter(question=question_item, user=request.user).first()
        if question_vote:
            question_item.user_vote = question_vote.value
        else:
            question_item.user_vote = 0

    # 4. Пагинация ответов (по 5 штук на страницу)
    page_obj = paginate(answers_list, request, per_page=5)

    context = {
        'question': question_item,
        'answers': page_obj,
        'form': form
    }
    return render(request, 'app/question.html', context)

@login_required(login_url='/login/')
def ask(request):
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            # Сохраняем вопрос без тегов (commit=False), так как ManyToMany нельзя сохранять сразу
            question_obj = form.save(commit=False)
            question_obj.author = request.user
            question_obj.save()

            # Обрабатываем строку тегов
            tags_string = form.cleaned_data.get('tags', '')
            # Разделяем строку по пробелам или запятым
            raw_tags = [t.strip().lower() for t in tags_string.replace(',', ' ').split() if t.strip()]

            # Берем первые 5 тегов для защиты от спама
            for tag_name in raw_tags[:5]:
                tag_obj, created = Tag.objects.get_or_create(name=tag_name)
                question_obj.tags.add(tag_obj)

            return redirect('question', question_id=question_obj.id)
    else:
        form = AskForm()

    return render(request, 'app/ask.html', {'form': form})


@require_POST
def like(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'auth_required',
            'message': 'Чтобы голосовать, необходимо войти в аккаунт.'
        }, status=401)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        vote_type = data.get('vote_type')  # Прилетит 'like' или 'dislike'

        if not question_id or vote_type not in ['like', 'dislike']:
            return JsonResponse({'error': 'bad_request', 'message': 'Неверные параметры'}, status=400)

        question = get_object_or_404(Question, id=question_id)
        target_value = 1 if vote_type == 'like' else -1

        # Ищем, голосовал ли уже этот пользователь за этот вопрос
        existing_vote = QuestionLike.objects.filter(user=request.user, question=question).first()

        if existing_vote:
            if existing_vote.value == target_value:
                # ОЦЕНКА СОВПАДАЕТ -> Повторный клик по той же кнопке (ОТМЕНА)
                question.rating -= existing_vote.value  # Убираем влияние старого голоса из рейтинга
                existing_vote.delete()  # Удаляем лайк/дизлайк из БД
                current_user_vote = 0  # Теперь у пользователя нет голоса
            else:
                # ОЦЕНКА ОТЛИЧАЕТСЯ -> Переголосование (с Лайка на Дизлайк или наоборот)
                question.rating -= existing_vote.value  # Сначала вычитаем старое значение
                existing_vote.value = target_value  # Меняем оценку на новую
                existing_vote.save()
                question.rating += target_value  # Добавляем новое значение
                current_user_vote = target_value
        else:
            # ГОЛОСА ЕЩЕ НЕ БЫЛО -> Создаем новую запись
            QuestionLike.objects.create(user=request.user, question=question, value=target_value)
            question.rating += target_value
            current_user_vote = target_value

        question.save()
        return JsonResponse({
            'rating': question.rating,
            'user_vote': current_user_vote  # Возвращаем 1, -1 или 0, чтобы JS обновил кнопки
        })

    except Exception as e:
        return JsonResponse({'error': 'server_error', 'message': 'Ошибка на сервере.'}, status=500)

@require_POST
def answer_like(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'auth_required',
            'message': 'Чтобы голосовать за ответы, необходимо войти в аккаунт.'
        }, status=401)

    try:
        data = json.loads(request.body)
        answer_id = data.get('question_id') # В JS мы передаем id как question_id, чтобы не плодить переменные
        vote_type = data.get('vote_type')

        if not answer_id or vote_type not in ['like', 'dislike']:
            return JsonResponse({'error': 'bad_request', 'message': 'Неверные параметры'}, status=400)

        answer_obj = get_object_or_404(Answer, id=answer_id)
        target_value = 1 if vote_type == 'like' else -1

        # Ищем существующий голос в AnswerLike
        existing_vote = AnswerLike.objects.filter(user=request.user, answer=answer_obj).first()

        if existing_vote:
            if existing_vote.value == target_value:
                answer_obj.rating -= existing_vote.value
                existing_vote.delete()
                current_user_vote = 0
            else:
                answer_obj.rating -= existing_vote.value
                existing_vote.value = target_value
                existing_vote.save()
                answer_obj.rating += target_value
                current_user_vote = target_value
        else:
            AnswerLike.objects.create(user=request.user, answer=answer_obj, value=target_value)
            answer_obj.rating += target_value
            current_user_vote = target_value

        answer_obj.save()
        return JsonResponse({
            'rating': answer_obj.rating,
            'user_vote': current_user_vote
        })

    except Exception as e:
        logger.error(f"Ошибка в view лайка ответа: {str(e)}")
        return JsonResponse({'error': 'server_error', 'message': 'Ошибка на сервере.'}, status=500)


@require_POST
def mark_correct(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required', 'message': 'Требуется авторизация.'}, status=401)

    try:
        data = json.loads(request.body)
        answer_id = data.get('answer_id')

        if not answer_id:
            return JsonResponse({'error': 'bad_request', 'message': 'ID ответа не передан.'}, status=400)

        answer_obj = get_object_or_404(Answer, id=answer_id)
        question_obj = answer_obj.question

        # КРИТИЧЕСКАЯ ПРОВЕРКА: только автор вопроса имеет право отмечать ответ!
        if question_obj.author != request.user:
            return JsonResponse({
                'error': 'forbidden',
                'message': 'Только автор вопроса может отмечать правильные ответы.'
            }, status=403)

        # Переключаем статус (если был правильным — станет неправильным, и наоборот)
        answer_obj.is_correct = not answer_obj.is_correct
        answer_obj.save()

        return JsonResponse({
            'status': 'success',
            'is_correct': answer_obj.is_correct
        })

    except Exception as e:
        logger.error(f"Ошибка в view отметки ответа: {str(e)}")
        return JsonResponse({'error': 'server_error', 'message': 'Ошибка на сервере.'}, status=500)