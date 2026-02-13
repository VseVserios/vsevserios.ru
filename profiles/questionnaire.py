from __future__ import annotations

from django.db.models import Prefetch, Q
from django.db.utils import OperationalError, ProgrammingError

SCALE_CHOICES = [
    ("1", "Совсем не про меня"),
    ("2", "Скорее не про меня"),
    ("3", "50/50"),
    ("4", "Скорее про меня"),
    ("5", "Полностью про меня"),
]

BUDGET_CHOICES = [
    ("low", "Низкие"),
    ("mid", "Средние"),
    ("high", "Высокие"),
    ("flex", "Гибко / зависит от ситуации"),
]

ROLE_CHOICES = [
    ("trad", "Традиционные"),
    ("mix", "Смешанные"),
    ("eq", "Партнёрские (50/50)"),
]

LANGUAGE_CHOICES = [
    ("words", "Слова"),
    ("time", "Время"),
    ("touch", "Прикосновения"),
    ("care", "Забота/помощь"),
    ("gifts", "Подарки"),
]

YESNO_CHOICES = [
    ("yes", "Да"),
    ("no", "Нет"),
    ("maybe", "Иногда / зависит"),
]

QUESTIONNAIRE_SPEC = [
    {
        "id": "principles",
        "title": "Жизненные принципы",
        "questions": [
            {"id": "principles_01", "text": "Честность важнее, чем удобство", "choices": SCALE_CHOICES},
            {"id": "principles_02", "text": "Я ценю свободу и личные границы", "choices": SCALE_CHOICES},
            {"id": "principles_03", "text": "Семья для меня в приоритете", "choices": SCALE_CHOICES},
            {"id": "principles_04", "text": "Я умею признавать ошибки", "choices": SCALE_CHOICES},
            {"id": "principles_05", "text": "Мне важна духовность/смысл", "choices": SCALE_CHOICES},
            {"id": "principles_06", "text": "Я избегаю конфликтов любой ценой", "choices": SCALE_CHOICES},
            {"id": "principles_07", "text": "Я готов(а) к компромиссам", "choices": SCALE_CHOICES},
            {"id": "principles_08", "text": "Для меня важны традиции", "choices": SCALE_CHOICES},
            {"id": "principles_09", "text": "Я предпочитаю стабильность риску", "choices": SCALE_CHOICES},
            {"id": "principles_10", "text": "Я быстро восстанавливаюсь после стресса", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "housing",
        "title": "Жилищные условия",
        "questions": [
            {"id": "housing_01", "text": "Мне важно жить отдельно от родителей", "choices": SCALE_CHOICES},
            {"id": "housing_02", "text": "Я люблю порядок и системность дома", "choices": SCALE_CHOICES},
            {"id": "housing_03", "text": "Я готов(а) к совместному быту сразу", "choices": SCALE_CHOICES},
            {"id": "housing_04", "text": "Мне нужен личный угол/пространство", "choices": SCALE_CHOICES},
            {"id": "housing_05", "text": "Я нормально отношусь к гостям дома", "choices": SCALE_CHOICES},
            {"id": "housing_06", "text": "Мне важно, чтобы дома было тихо", "choices": SCALE_CHOICES},
            {"id": "housing_07", "text": "Дом для меня — место восстановления", "choices": SCALE_CHOICES},
            {"id": "housing_08", "text": "Я люблю готовить дома", "choices": SCALE_CHOICES},
            {"id": "housing_09", "text": "Мне важно иметь собственное жильё", "choices": SCALE_CHOICES},
            {"id": "housing_10", "text": "Я готов(а) к переезду ради отношений", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "roles",
        "title": "Роли",
        "questions": [
            {"id": "roles_01", "text": "Какой формат ролей в паре комфортен", "choices": ROLE_CHOICES},
            {"id": "roles_02", "text": "Мне комфортно быть лидером в паре", "choices": SCALE_CHOICES},
            {"id": "roles_03", "text": "Мне комфортно следовать за партнёром", "choices": SCALE_CHOICES},
            {"id": "roles_04", "text": "Решения должны приниматься вместе", "choices": SCALE_CHOICES},
            {"id": "roles_05", "text": "Мне важно распределение обязанностей", "choices": SCALE_CHOICES},
            {"id": "roles_06", "text": "Я люблю заботиться о партнёре", "choices": SCALE_CHOICES},
            {"id": "roles_07", "text": "Мне важна инициатива партнёра", "choices": SCALE_CHOICES},
            {"id": "roles_08", "text": "Я хочу, чтобы у каждого были свои зоны", "choices": SCALE_CHOICES},
            {"id": "roles_09", "text": "Я хочу общие цели на 3–5 лет", "choices": SCALE_CHOICES},
            {"id": "roles_10", "text": "Мне важно уважение к моим решениям", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "work",
        "title": "Работа",
        "questions": [
            {"id": "work_01", "text": "Я амбициозен/амбициозна", "choices": SCALE_CHOICES},
            {"id": "work_02", "text": "Для меня важна карьера", "choices": SCALE_CHOICES},
            {"id": "work_03", "text": "Я готов(а) много работать ради цели", "choices": SCALE_CHOICES},
            {"id": "work_04", "text": "Я предпочитаю work-life balance", "choices": SCALE_CHOICES},
            {"id": "work_05", "text": "Мне важно, чтобы партнёр развивался", "choices": SCALE_CHOICES},
            {"id": "work_06", "text": "Я хочу/готов(а) поддерживать партнёра в карьере", "choices": SCALE_CHOICES},
            {"id": "work_07", "text": "Я открыт(а) к переезду из-за работы", "choices": SCALE_CHOICES},
            {"id": "work_08", "text": "Мне важно иметь свой проект/дело", "choices": SCALE_CHOICES},
            {"id": "work_09", "text": "Я стабилен(а) в доходах", "choices": SCALE_CHOICES},
            {"id": "work_10", "text": "Я готов(а) к совместным финансовым целям", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "wife_expenses",
        "title": "Расходы на жену",
        "questions": [
            {"id": "wife_expenses_01", "text": "Уровень расходов/подарков", "choices": BUDGET_CHOICES},
            {"id": "wife_expenses_02", "text": "Мужчина должен полностью обеспечивать", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_03", "text": "Я за общий бюджет", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_04", "text": "Я за раздельный бюджет", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_05", "text": "Траты должны обсуждаться заранее", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_06", "text": "Мне важны регулярные подарки", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_07", "text": "Мне важны совместные поездки", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_08", "text": "Я готов(а) инвестировать в образование партнёра", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_09", "text": "Я готов(а) поддерживать родных партнёра", "choices": SCALE_CHOICES},
            {"id": "wife_expenses_10", "text": "Мне важна финансовая безопасность", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "sexual",
        "title": "Сексуальная совместимость",
        "questions": [
            {"id": "sexual_01", "text": "Интим — важная часть отношений", "choices": SCALE_CHOICES},
            {"id": "sexual_02", "text": "Мне важно обсуждать желания", "choices": SCALE_CHOICES},
            {"id": "sexual_03", "text": "Я комфортно говорю о границах", "choices": SCALE_CHOICES},
            {"id": "sexual_04", "text": "Мне важна нежность", "choices": SCALE_CHOICES},
            {"id": "sexual_05", "text": "Мне важна страсть", "choices": SCALE_CHOICES},
            {"id": "sexual_06", "text": "Я открыт(а) к экспериментам", "choices": SCALE_CHOICES},
            {"id": "sexual_07", "text": "Я предпочитаю стабильность", "choices": SCALE_CHOICES},
            {"id": "sexual_08", "text": "Я ценю инициативу партнёра", "choices": SCALE_CHOICES},
            {"id": "sexual_09", "text": "Мне важна эмоциональная близость", "choices": SCALE_CHOICES},
            {"id": "sexual_10", "text": "Мне важна совместимость по темпераменту", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "rest",
        "title": "Отдых",
        "questions": [
            {"id": "rest_01", "text": "Я люблю активный отдых", "choices": SCALE_CHOICES},
            {"id": "rest_02", "text": "Я люблю спокойный отдых", "choices": SCALE_CHOICES},
            {"id": "rest_03", "text": "Я люблю путешествия", "choices": SCALE_CHOICES},
            {"id": "rest_04", "text": "Мне важны совместные хобби", "choices": SCALE_CHOICES},
            {"id": "rest_05", "text": "Мне нужно иногда отдыхать отдельно", "choices": SCALE_CHOICES},
            {"id": "rest_06", "text": "Я люблю спонтанность", "choices": SCALE_CHOICES},
            {"id": "rest_07", "text": "Я люблю планировать заранее", "choices": SCALE_CHOICES},
            {"id": "rest_08", "text": "Мне важны вечерние прогулки/встречи", "choices": SCALE_CHOICES},
            {"id": "rest_09", "text": "Я люблю мероприятия и тусовки", "choices": SCALE_CHOICES},
            {"id": "rest_10", "text": "Мне важен здоровый сон и режим", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "love_language",
        "title": "Язык любви",
        "questions": [
            {"id": "love_language_01", "text": "Мой главный язык любви", "choices": LANGUAGE_CHOICES},
            {"id": "love_language_02", "text": "Мне важны слова поддержки", "choices": SCALE_CHOICES},
            {"id": "love_language_03", "text": "Мне важно качественное время вместе", "choices": SCALE_CHOICES},
            {"id": "love_language_04", "text": "Мне важны прикосновения", "choices": SCALE_CHOICES},
            {"id": "love_language_05", "text": "Мне важны действия/забота", "choices": SCALE_CHOICES},
            {"id": "love_language_06", "text": "Мне важны подарки", "choices": SCALE_CHOICES},
            {"id": "love_language_07", "text": "Я люблю делать сюрпризы", "choices": SCALE_CHOICES},
            {"id": "love_language_08", "text": "Я люблю говорить о чувствах", "choices": SCALE_CHOICES},
            {"id": "love_language_09", "text": "Мне важно слышать признание", "choices": SCALE_CHOICES},
            {"id": "love_language_10", "text": "Мне важны совместные ритуалы", "choices": SCALE_CHOICES},
        ],
    },
    {
        "id": "tests",
        "title": "Тесты",
        "questions": [
            {
                "id": "tests_01",
                "text": "Представьте гипотетическую ситуацию. Если ваш 7-и летний сын разобьёт окно в доме соседей, кто будет отвечать перед соседями за содеяное",
                "choices": [
                    ("1", "Отец (т.к. его дети находятся под его защитой)"),
                    ("2", "Мать (вырастила мягкотелого, пусть теперь пожинает плоды)"),
                    ("3", "Сам будет отвечать (за свои поступки должен брать ответственность на себя)"),
                    ("4", "Отец и мать (оба воспитывали — обоим и отвечать)"),
                    ("5", "Бабушка (она больше всех проводит с ним времени, поэтому ей и отвечать)"),
                    ("6", "Дедушка (т.к. он избаловал внука)"),
                    ("7", "Никто ничего не узнает"),
                ],
            },
            {
                "id": "tests_02",
                "text": "Представьте гипотетическую ситуацию. Вас с женой пригласили на вечеринку. Вы едете на неё с работы и опаздывает, а жена едет из дома и приезжает вовремя. Вы заходите на вечеринку и перед вами разворачивается следующая картина: ваша жена буянит, ведёт  себя неадекватно, со всеми ругаться, лезет в драку с мужиками, старается плюнуть им в лицо. Вы быстро оцениваете ситуацию и понимаете, что ваша жена целиком и полностью НЕ права.",
                "choices": [
                    (
                        "1",
                        "Подбегу к жене, тряхну её за плечи, извинюсь перед всеми, отведу жену в туалет и объясню ей, что вести себя так при людях нельзя",
                    ),
                    ("2", "Молча возьму жену в охабку и отвезу домой, там ей всё объясню"),
                    (
                        "3",
                        "При любом раскладе заступлюсь за жену: кому пыталась набить морду — набью сам; кому пыталась плюнуть в лицо — плюну сам; кто её оскорблял — ответит за каждое слово не отходя от кассы. Потом отвезу её домой и дома, без свидетелей, доходчиво объясню, что так поступать нельзя.",
                    ),
                    (
                        "4",
                        "С радостью набью всем морду, скажу жене спасибо (за то, что знает как меня порадовать) и продолжу танцевать с теми, кто ещё останется на вечеринке.",
                    ),
                    ("5", "Сделаю вид, что это не моя жена. Слава богу, что никто из присутствующих не видел нас вместе."),
                    (
                        "6",
                        "При всех силой остановлю жену и на месте, при всех (чтобы ей было стыдно) объясню, что с таким поведением она больше из дома не выйдет.",
                    ),
                    (
                        "7",
                        "Попрошу друзей помочь её схватить, связать и вызвать психиатрическую скорую помощь.",
                    ),
                    ("8", "Сяду за свободный столик и буду наблюдать за тем, чем это всё закончится."),
                    (
                        "9",
                        'Подойду поближе и выкриками: "Люся давай, разнеси здесь всё на..ер" буду поддерживать свою жену. Ведь после таких гулянок жена неделю ходит спокойная как удав.',
                    ),
                ],
            },
            {
                "id": "tests_03",
                "text": "Представьте гипотетическую ситуацию. Вашего мужа уволили с работы, он расстроен и подавлен. Разочаровался в себе и в окружающих",
                "choices": [
                    ("1", "Пойду работать сама, ведь у нас двое детей и ипотека."),
                    (
                        "2",
                        "Буду вдохновлять мужа, окажу моральную поддержку, помогу скорее взять себя в руки и найти новую работу. Помогу осознать то, что на его могучих плечах держится весь мир, который он сам построил: дети, жена, престарелая мать и ипотека.",
                    ),
                    (
                        "3",
                        "Возьму новый кредит, кредитная история хорошая, несколько месяцев мы протянем, дальше будет видно.",
                    ),
                    ("4", "Выгоню мужа из дома, буду решать свои проблемы сама, слава богу мама научила."),
                    ("5", "Разведусь и уйду к другому, более успешному (давно меня звал)."),
                    (
                        "6",
                        "Позову маму в гости, она сможет замотивировать зятя на поиски новой работы.",
                    ),
                    (
                        "7",
                        "Попрошу папу пристроить мужа у него в фирме. Он меня любит и никогда не откажет.",
                    ),
                    (
                        "8",
                        "Объясню старшему сыну, что теперь семья на нём и его обязанность теперь за всё платить.",
                    ),
                    (
                        "9",
                        "Выставлю квартиру на продажу, других вариантов нет, надеяться больше не на кого.",
                    ),
                ],
            },
        ],
    },
]


def get_questionnaire_spec(gender: str | None = None):
    try:
        from .models import QuestionnaireChoice, QuestionnaireQuestion, QuestionnaireSection

        if not QuestionnaireSection.objects.exists():
            return QUESTIONNAIRE_SPEC

        gender_value = (str(gender).strip() if gender is not None else "") or None

        sections_qs = QuestionnaireSection.objects.order_by("order", "id")
        questions_qs = QuestionnaireQuestion.objects.order_by("order", "id")

        if gender_value is not None:
            sections_qs = sections_qs.filter(Q(gender="") | Q(gender=gender_value))
            questions_qs = questions_qs.filter(Q(gender="") | Q(gender=gender_value))

        sections_qs = sections_qs.prefetch_related(
            Prefetch(
                "questions",
                queryset=questions_qs.prefetch_related(
                    Prefetch(
                        "choices",
                        queryset=QuestionnaireChoice.objects.order_by("order", "id"),
                    )
                ),
            )
        )

        spec = []
        for section in sections_qs:
            questions = []
            for q in section.questions.all():
                choices = [(c.value, c.label) for c in q.choices.all()]
                questions.append(
                    {
                        "id": q.code,
                        "text": q.text,
                        "input_type": (getattr(q, "input_type", None) or "choice"),
                        "choices": choices,
                        "is_multiple": q.is_multiple,
                    }
                )
            if not questions:
                continue
            spec.append({"id": section.code, "title": section.title, "questions": questions})
        return spec
    except (OperationalError, ProgrammingError):
        return QUESTIONNAIRE_SPEC


def questionnaire_gender_for_profile(profile, kind: str) -> str | None:
    if kind == "me":
        value = getattr(profile, "gender", None)
        return (str(value).strip() if value is not None else "") or None

    if kind == "ideal":
        looking_for = getattr(profile, "looking_for", None)
        looking_for_value = (str(looking_for).strip() if looking_for is not None else "") or None
        if looking_for_value == "men":
            return "male"
        if looking_for_value == "women":
            return "female"
        return None

    raise ValueError("Invalid questionnaire kind")


def get_questionnaire_spec_for_profile(profile, kind: str):
    return get_questionnaire_spec(questionnaire_gender_for_profile(profile, kind))


def questionnaire_total(spec=None):
    spec = spec or get_questionnaire_spec()
    return sum(len(section.get("questions") or []) for section in spec)


def iter_question_ids(spec=None):
    spec = spec or get_questionnaire_spec()
    for section in spec:
        for q in section.get("questions") or []:
            yield q["id"]


def questionnaire_progress(answers: dict | None, spec=None):
    answers = answers or {}
    spec = spec or get_questionnaire_spec()

    answered = 0
    for qid in iter_question_ids(spec):
        v = answers.get(qid)
        if v is None:
            continue
        if isinstance(v, (list, tuple, set)):
            if any((x is not None and str(x).strip() != "") for x in v):
                answered += 1
            continue
        if str(v).strip() != "":
            answered += 1
    total = questionnaire_total(spec)
    percent = int(round((answered / total) * 100)) if total else 0
    return answered, total, percent
