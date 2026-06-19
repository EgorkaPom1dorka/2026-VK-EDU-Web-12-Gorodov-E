import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile
from app.models import Question, Answer, Tag
from faker import Faker


class Command(BaseCommand):
    help = 'Заполняет БД большим объемом осмысленных IT-данных (200 вопросов, от 10 ответов к каждому)'

    def handle(self, *args, **options):
        fake = Faker(['ru_RU'])

        self.stdout.write(self.style.WARNING('Очистка старых данных...'))
        Question.objects.all().delete()
        Answer.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('База очищена! Начинаем масштабную генерацию...'))

        # Популярные теги
        tag_names = ['python', 'django', 'mysql', 'postgres', 'docker', 'bootstrap', 'javascript', 'git', 'web',
                     'linux']
        tags_pool = {}
        for name in tag_names:
            t, _ = Tag.objects.get_or_create(name=name)
            tags_pool[name] = t

        # Реалистичные заготовки для вопросов
        it_questions_templates = [
            {
                "title": "Как исправить ошибку 'N+1 запросов' в Django ORM?",
                "text": "Заметил по логам, что при выводе списка постов с авторами Django делает отдельный SQL-запрос к профилю каждого пользователя. Как это оптимизировать и объединить в один запрос?",
                "tags": ['python', 'django', 'postgres']
            },
            {
                "title": "В чем разница между операторами == и is в Python?",
                "text": "Пишу условие проверки объектов, иногда `is` срабатывает странно для больших чисел или одинаковых строк. Объясните, пожалуйста, разницу на пальцах, как они работают с памятью?",
                "tags": ['python']
            },
            {
                "title": "Как пробросить порты из контейнера Docker на локальную машину?",
                "text": "Запустил контейнер с MySQL внутри Docker, но не могу подключиться к нему через DataGrip с хост-машины. Какой флаг или настройку в docker-compose нужно использовать?",
                "tags": ['docker', 'mysql']
            },
            {
                "title": "Ошибки кодировки utf8mb4 в базе данных MySQL",
                "text": "Пытаюсь сохранить смайлики emoji в текстовое поле таблицы, но база пападают с ошибкой Incorrect string value. Настройки базы стоят дефолтные. Куда копать?",
                "tags": ['mysql', 'web']
            },
            {
                "title": "Как сделать липкий футер (Sticky Footer) на Bootstrap 5?",
                "text": "Когда на странице мало контента, футер поднимается к середине экрана. Хочу, чтобы он всегда был прижат к самому низу окна браузера. Какие классы обертки применить?",
                "tags": ['bootstrap', 'web']
            },
            {
                "title": "Почему async/await в JavaScript работает асинхронно?",
                "text": "Пытаюсь разобраться в Event Loop. Блокирует ли async функция выполнение основного потока или нет, если внутри нее запустить тяжелый цикл вычислений?",
                "tags": ['javascript', 'web']
            },
            {
                "title": "Как отменить последний коммит в Git, если он еще не отправлен в push?",
                "text": "Случайно закоммитил отладочные логи в ветку main. Коммит локальный, на GitHub не улетал. Как правильно откатить состояние, чтобы сохранить изменения в файлах?",
                "tags": ['git']
            },
            {
                "title": "Разница между типом данных TEXT и VARCHAR в PostgreSQL",
                "text": "Планирую архитектуру под хранение длинных статей. Есть ли в Postgres разница по производительности между VARCHAR(M) и обычным TEXT, или это миф из MySQL?",
                "tags": ['postgres']
            },
            {
                "title": "Как настроить автозапуск скрипта при старте системы в Ubuntu Linux?",
                "text": "Написал небольшого бота на Python, хочу чтобы он автоматически поднимался как демон при перезагрузке сервера. Лучше использовать systemd или crontab?",
                "tags": ['linux', 'python']
            },
            {
                "title": "Не подгружаются статические файлы CSS в Django при DEBUG=False",
                "text": "Локально на компе все стили работают, но как только выключаю режим отладки в settings.py, верстка ломается и сервер выдает 404 на все css/js файлы. В чем проблема?",
                "tags": ['django', 'web']
            }
        ]

        answers_pool = {
            'django': [
                "Используйте метод `.select_related()` для ForeignKey полей или `.prefetch_related()` для ManyToMany связей. Это сделает один `JOIN` запрос вместо сотни.",
                "Проверьте, установлена ли у вас настройка `STATIC_ROOT` и запускали ли вы команду `python manage.py collectstatic` перед выключением дебага.",
                "Рекомендую поставить библиотеку `django-debug-toolbar`. Она наглядно показывает дубликаты SQL-запросов прямо на странице в браузере."
            ],
            'python': [
                "Оператор `==` проверяет равенство значений объектов (вызывает метод `__eq__`), а `is` проверяет идентичность в памяти (совпадение их `id`).",
                "Для демонизации в Linux лучше использовать `systemd`. Создайте `.service` файл в `/etc/systemd/system/`, это самый надежный и современный стандарт.",
                "Числа от -5 до 256 кэшируются Python при старте, поэтому для них `is` вернет True. Для больших чисел это работать не будет, используйте `==`."
            ],
            'docker': [
                "Вам нужно использовать маппинг портов в секции `ports:` вашего `docker-compose.yml`. Например: `- 3306:3306`.",
                "Убедись, что внутри контейнера MySQL слушает адрес `0.0.0.0`, а не `127.0.0.1`, иначе извне к нему достучаться не получится."
            ],
            'mysql': [
                "Вам нужно изменить кодировку самой базы данных, таблицы и конкретного поля на `utf8mb4` и сопоставление `utf8mb4_unicode_ci`.",
                "Не забудьте в строке подключения (DATABASE URL) тоже указать правильный charset, иначе драйвер будет принудительно слать старый кодировщик."
            ],
            'bootstrap': [
                "Добавьте класс `d-flex flex-column min-vh-100` на тег `<body>`, а футеру задайте класс `mt-auto`. Bootstrap сделает все остальное автоматически.",
                "Можно обернуть весь контент кроме футера в блок с классом `flex-grow-1`, тогда футер вытолкнется строго к нижней границе экрана."
            ],
            'git': [
                "Используйте команду `git reset --soft HEAD~1`. Флаг `--soft` удалит сам коммит, но сохранит все ваши измененные файлы в рабочей зоне.",
                "Если нужно уничтожить коммит безвозвратно вместе с кодом, пишите `git reset --hard HEAD~1`. Будьте аккуратны, код сотрется!"
            ]
        }
        default_answers = [
            "Отличное объяснение, спасибо! Тоже столкнулся с этой проблемой вчера.",
            "Попробуйте заглянуть в официальную документацию, там этот момент подробно расписан со всеми примерами.",
            "Мне помог полный перезапуск сервера и очистка кэша браузера через Ctrl+F5."
        ]

        # Создаем пользователей (увеличим до 50, чтобы авторы чаще чередовались)
        users = []
        self.stdout.write('Создание авторов...')
        for _ in range(50):
            username = fake.unique.user_name()
            user = User.objects.create_user(
                username=username,
                email=fake.unique.email(),
                password='password123'
            )
            Profile.objects.get_or_create(user=user)
            users.append(user)

        # Генерируем 200 вопросов
        self.stdout.write('Создание 200 осмысленных вопросов...')
        start_date = datetime.now() - timedelta(days=120)

        for i in range(200):
            author = random.choice(users)
            template = it_questions_templates[i % len(it_questions_templates)]

            random_days = random.randint(0, 120)
            created_at = start_date + timedelta(days=random_days)
            rating = random.randint(-5, 80)

            # Добавляем уникальные маркеры, чтобы 200 вопросов не выглядели абсолютно одинаково
            title_postfix = f" (Кейс #{100 + i})"
            intro_text = random.choice([
                "Привет всем! ", "Столкнулся со следующей проблемой. ",
                "Коллеги, нужен ваш совет. ", "Разрабатываю проект и ", ""
            ])

            q = Question.objects.create(
                title=template["title"] + title_postfix,
                text=intro_text + template["text"],
                author=author,
                rating=rating,
            )
            Question.objects.filter(pk=q.pk).update(created_at=created_at)

            q_tags = [tags_pool[name] for name in template["tags"]]
            q.tags.set(q_tags)

            # Генерируем МИНИМУМ 10 ответов к каждому вопросу (диапазон от 10 до 14)
            main_tag = template["tags"][0]
            possible_answers = answers_pool.get(main_tag, default_answers) + default_answers

            random.shuffle(possible_answers)

            answers_to_create = random.randint(10, 14)
            for j in range(answers_to_create):
                ans_author = random.choice(users)
                ans_created = q.created_at + timedelta(hours=random.randint(1, 48))

                prefix = random.choice(
                    ["Думаю, что ", "Попробуйте так: ", "Слушайте, ", "О, классный вопрос. ", "Обычно делают так: ",
                     ""])
                ans_text = prefix + possible_answers[j % len(possible_answers)]

                ans = Answer.objects.create(
                    question=q,
                    text=ans_text,
                    author=ans_author,
                    rating=random.randint(0, 25),
                    is_correct=(j == 0 and random.choice([True, False, False]))
                )
                Answer.objects.filter(pk=ans.pk).update(created_at=ans_created)

        self.stdout.write(
            self.style.SUCCESS('Готово! Успешно сгенерировано 200 IT-вопросов и более 2000 ответов к ним.'))