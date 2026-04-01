from functools import lru_cache

from profiles.questionnaire import get_questionnaire_spec, questionnaire_gender_for_profile


def build_question_specs(spec=None):
    spec = spec or get_questionnaire_spec()
    specs = {}
    for section in spec:
        for q in section.get("questions") or []:
            specs[q["id"]] = q
    return specs


@lru_cache(maxsize=8)
def _allowed_question_ids_for_gender(gender: str | None):
    spec = get_questionnaire_spec(gender)
    ids = []
    for section in spec:
        for q in section.get("questions") or []:
            ids.append(q["id"])
    return frozenset(ids)


def _normalize(value):
    if value is None:
        return None
    v = str(value).strip()
    if v == "":
        return None
    return v


def _normalize_many(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        items = [str(x).strip() for x in value if x is not None and str(x).strip() != ""]
        return items or None
    v = _normalize(value)
    return [v] if v is not None else None


def _choice_values(spec):
    return [str(v) for v, _ in spec.get("choices") or []]


def _score_single_answer(spec, expected: str, actual: str):
    values = _choice_values(spec)

    is_scale = set(values) == {"1", "2", "3", "4", "5"}
    if is_scale and expected.isdigit() and actual.isdigit():
        e = int(expected)
        a = int(actual)
        if e < 1 or e > 5 or a < 1 or a > 5:
            return 0.0
        diff = abs(e - a)
        return max(0.0, 1.0 - (diff / 4.0))

    is_yesno = set(values) == {"yes", "no", "maybe"}
    if is_yesno:
        if expected == actual:
            return 1.0
        if expected == "maybe" or actual == "maybe":
            return 0.5
        return 0.0

    return 1.0 if expected == actual else 0.0


def _score_multiple_answer(expected_items: list[str], actual_items: list[str]):
    e = {str(x).strip() for x in (expected_items or []) if str(x).strip() != ""}
    a = {str(x).strip() for x in (actual_items or []) if str(x).strip() != ""}
    if not e or not a:
        return None
    inter = len(e & a)
    union = len(e | a)
    if union == 0:
        return None
    return inter / union


def _score_question(spec: dict, expected_answers: dict, actual_answers: dict):
    if (spec.get("input_type") or "choice") == "text":
        return None

    qid = spec.get("id")
    is_multiple = bool(spec.get("is_multiple"))
    if is_multiple:
        expected_many = _normalize_many(expected_answers.get(qid))
        actual_many = _normalize_many(actual_answers.get(qid))
        if expected_many is None or actual_many is None:
            return None
        score = _score_multiple_answer(expected_many, actual_many)
        if score is None:
            return None
        return {
            "score": float(score),
            "expected": expected_many,
            "actual": actual_many,
        }

    expected = _normalize(expected_answers.get(qid))
    actual = _normalize(actual_answers.get(qid))
    if expected is None or actual is None:
        return None
    return {
        "score": float(_score_single_answer(spec, expected, actual)),
        "expected": expected,
        "actual": actual,
    }


def compatibility_breakdown(profile_a, profile_b, spec=None):
    """Compatibility report grouped by questionnaire sections.

    Returns per-section percents plus question-level details for both directions:
    A(ideal)->B(me) and B(ideal)->A(me).
    """

    spec = spec or get_questionnaire_spec()

    a_ideal_gender = questionnaire_gender_for_profile(profile_a, "ideal")
    a_me_gender = questionnaire_gender_for_profile(profile_a, "me")
    b_me_gender = questionnaire_gender_for_profile(profile_b, "me")
    a_ideal_allowed = _allowed_question_ids_for_gender(a_ideal_gender)
    a_me_allowed = _allowed_question_ids_for_gender(a_me_gender)
    b_me_allowed = _allowed_question_ids_for_gender(b_me_gender)

    b_ideal_gender = questionnaire_gender_for_profile(profile_b, "ideal")
    b_me_gender_for_expected = questionnaire_gender_for_profile(profile_b, "me")
    b_ideal_allowed = _allowed_question_ids_for_gender(b_ideal_gender)
    b_me_allowed = _allowed_question_ids_for_gender(b_me_gender_for_expected)
    a_me_allowed_for_actual = _allowed_question_ids_for_gender(a_me_gender)

    a_expected = profile_a.questionnaire_ideal or {}
    a_actual = profile_a.questionnaire_me or {}
    b_expected = profile_b.questionnaire_ideal or {}
    b_actual = profile_b.questionnaire_me or {}

    sections_out = []

    a_to_b_total = 0.0
    a_to_b_compared = 0
    b_to_a_total = 0.0
    b_to_a_compared = 0

    for section in spec:
        section_questions = section.get("questions") or []
        if not section_questions:
            continue

        questions_out = []

        s_a_to_b_total = 0.0
        s_a_to_b_compared = 0
        s_b_to_a_total = 0.0
        s_b_to_a_compared = 0

        for q in section_questions:
            qid = q.get("id")
            if not qid:
                continue

            show_in_ideal = bool(q.get("show_in_ideal", True))

            a_to_b_part = None
            b_to_a_part = None

            a_to_b_allowed = (a_ideal_allowed if show_in_ideal else a_me_allowed) & b_me_allowed
            if qid in a_to_b_allowed:
                a_to_b_part = _score_question(q, (a_expected if show_in_ideal else a_actual), b_actual)
                if a_to_b_part is not None:
                    s_a_to_b_total += float(a_to_b_part["score"])
                    s_a_to_b_compared += 1
                    a_to_b_total += float(a_to_b_part["score"])
                    a_to_b_compared += 1

            b_to_a_allowed = (b_ideal_allowed if show_in_ideal else b_me_allowed) & a_me_allowed_for_actual
            if qid in b_to_a_allowed:
                b_to_a_part = _score_question(q, (b_expected if show_in_ideal else b_actual), a_actual)
                if b_to_a_part is not None:
                    s_b_to_a_total += float(b_to_a_part["score"])
                    s_b_to_a_compared += 1
                    b_to_a_total += float(b_to_a_part["score"])
                    b_to_a_compared += 1

            if a_to_b_part is None and b_to_a_part is None:
                continue

            questions_out.append(
                {
                    "id": qid,
                    "text": q.get("text") or "",
                    "choices": q.get("choices") or [],
                    "input_type": q.get("input_type") or "choice",
                    "is_multiple": bool(q.get("is_multiple")),
                    "a_to_b": a_to_b_part,
                    "b_to_a": b_to_a_part,
                }
            )

        if not questions_out:
            continue

        s_a_to_b_percent = (
            int(round((s_a_to_b_total / s_a_to_b_compared) * 100)) if s_a_to_b_compared else None
        )
        s_b_to_a_percent = (
            int(round((s_b_to_a_total / s_b_to_a_compared) * 100)) if s_b_to_a_compared else None
        )

        section_parts = [p for p in (s_a_to_b_percent, s_b_to_a_percent) if p is not None]
        s_overall = int(round(sum(section_parts) / len(section_parts))) if section_parts else None

        sections_out.append(
            {
                "id": section.get("id") or "",
                "title": section.get("title") or "",
                "overall": s_overall,
                "a_to_b": s_a_to_b_percent,
                "b_to_a": s_b_to_a_percent,
                "a_compared": s_a_to_b_compared,
                "b_compared": s_b_to_a_compared,
                "questions": questions_out,
            }
        )

    a_to_b_percent = int(round((a_to_b_total / a_to_b_compared) * 100)) if a_to_b_compared else None
    b_to_a_percent = int(round((b_to_a_total / b_to_a_compared) * 100)) if b_to_a_compared else None
    parts = [p for p in (a_to_b_percent, b_to_a_percent) if p is not None]
    overall = int(round(sum(parts) / len(parts))) if parts else None

    return {
        "overall": overall,
        "a_to_b": a_to_b_percent,
        "b_to_a": b_to_a_percent,
        "a_compared": a_to_b_compared,
        "b_compared": b_to_a_compared,
        "sections": sections_out,
    }


def score_expected_vs_actual(
    expected_answers: dict | None,
    actual_answers: dict | None,
    question_specs: dict | None = None,
):
    expected_answers = expected_answers or {}
    actual_answers = actual_answers or {}

    question_specs = question_specs or build_question_specs()

    total = 0.0
    compared = 0

    for qid, spec in question_specs.items():
        if (spec.get("input_type") or "choice") == "text":
            continue

        is_multiple = bool(spec.get("is_multiple"))
        if is_multiple:
            expected_many = _normalize_many(expected_answers.get(qid))
            actual_many = _normalize_many(actual_answers.get(qid))
            if expected_many is None or actual_many is None:
                continue
            score = _score_multiple_answer(expected_many, actual_many)
            if score is None:
                continue
            total += float(score)
            compared += 1
        else:
            expected = _normalize(expected_answers.get(qid))
            actual = _normalize(actual_answers.get(qid))
            if expected is None or actual is None:
                continue
            total += _score_single_answer(spec, expected, actual)
            compared += 1

    if compared == 0:
        return None, 0

    percent = int(round((total / compared) * 100))
    return percent, compared


def compatibility(profile_a, profile_b, question_specs: dict | None = None):
    question_specs = question_specs or build_question_specs()

    a_ideal_gender = questionnaire_gender_for_profile(profile_a, "ideal")
    a_me_gender = questionnaire_gender_for_profile(profile_a, "me")
    b_ideal_gender = questionnaire_gender_for_profile(profile_b, "ideal")
    b_me_gender = questionnaire_gender_for_profile(profile_b, "me")

    a_ideal_allowed = _allowed_question_ids_for_gender(a_ideal_gender)
    a_me_allowed = _allowed_question_ids_for_gender(a_me_gender)
    b_ideal_allowed = _allowed_question_ids_for_gender(b_ideal_gender)
    b_me_allowed = _allowed_question_ids_for_gender(b_me_gender)

    a_total = 0.0
    a_compared = 0
    b_total = 0.0
    b_compared = 0

    a_expected = profile_a.questionnaire_ideal or {}
    a_me = profile_a.questionnaire_me or {}
    b_expected = profile_b.questionnaire_ideal or {}
    b_me = profile_b.questionnaire_me or {}

    for qid, qspec in (question_specs or {}).items():
        if (qspec.get("input_type") or "choice") == "text":
            continue

        show_in_ideal = bool(qspec.get("show_in_ideal", True))

        a_allowed = (a_ideal_allowed if show_in_ideal else a_me_allowed) & b_me_allowed
        if qid in a_allowed:
            part = _score_question(qspec, (a_expected if show_in_ideal else a_me), b_me)
            if part is not None:
                a_total += float(part["score"])
                a_compared += 1

        b_allowed = (b_ideal_allowed if show_in_ideal else b_me_allowed) & a_me_allowed
        if qid in b_allowed:
            part = _score_question(qspec, (b_expected if show_in_ideal else b_me), a_me)
            if part is not None:
                b_total += float(part["score"])
                b_compared += 1

    a_to_b = int(round((a_total / a_compared) * 100)) if a_compared else None
    b_to_a = int(round((b_total / b_compared) * 100)) if b_compared else None

    parts = [p for p in (a_to_b, b_to_a) if p is not None]
    overall = int(round(sum(parts) / len(parts))) if parts else None

    return {
        "overall": overall,
        "a_to_b": a_to_b,
        "b_to_a": b_to_a,
        "a_compared": a_compared,
        "b_compared": b_compared,
    }
