from decimal import Decimal

from django.db.models import Prefetch

from api.models import NegativeRemarkOnTask, Task

ALLOWED_KPI_STAGES = {
    Task.Stage.COMPLETE,
    Task.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
    Task.Stage.APPROVED,
}


def calculate_designer_monthly_kpi(designer_id, year, month) -> float:
    tasks = (
        Task.objects.filter(
            designer_id=designer_id,
            created_at__year=year,
            created_at__month=month,
            stage__in=ALLOWED_KPI_STAGES,
        )
        .select_related(
            "type_of_work",
            "revision_of__type_of_work",
            "redo_of__type_of_work",
        )
        .prefetch_related(
            Prefetch(
                "negative_remark_links",
                queryset=NegativeRemarkOnTask.objects.select_related("negative_remark").order_by("id"),
            )
        )
        .order_by("id")
    )

    grouped_tasks = {}
    for task in tasks:
        original_task = _resolve_original_task(task)
        if original_task is None:
            continue

        group = grouped_tasks.setdefault(
            original_task.id,
            {
                "original_task": original_task,
                "tasks": {},
            },
        )
        group["tasks"][task.id] = task

    total = Decimal("0")
    weekly_scores = {str(week): Decimal("0") for week in range(1, 6)}
    for group in grouped_tasks.values():
        related_tasks = list(group["tasks"].values())
        group_points = _calculate_group_points(group["original_task"], related_tasks)
        total += group_points
        weekly_scores[str(_resolve_group_week(group["original_task"], related_tasks))] += group_points

    return {
        "total_kpi_score": float(total),
        "weekly_scores": {
            week: float(value)
            for week, value in weekly_scores.items()
        },
    }


def _resolve_original_task(task):
    if task.revision_of_id:
        return task.revision_of
    if task.redo_of_id:
        return task.redo_of
    return task


def _calculate_group_points(original_task, related_tasks) -> Decimal:
    related_tasks = list(related_tasks)
    base_point = _to_decimal(getattr(original_task.type_of_work, "point", 0))
    max_slides = max((_to_int(task.slides) for task in related_tasks), default=0)
    slide_points = Decimal(max_slides) * base_point

    revision_points = Decimal("0")
    redo_points = Decimal("0")
    excellence_points = Decimal("0")
    negative_points = Decimal("0")

    for task in related_tasks:
        if task.revision_of_id:
            revision_points += _calculate_revision_points(task)
        if task.redo_of_id:
            redo_points += _to_decimal(getattr(task.type_of_work, "redo_point", 0))

        excellence_points += _to_decimal(task.excellence)
        negative_points += _calculate_negative_points(task)

    return slide_points + revision_points + redo_points + excellence_points - negative_points


def _resolve_group_week(original_task, related_tasks) -> int:
    dated_tasks = [task for task in related_tasks if task.created_at]
    if original_task in dated_tasks:
        reference_date = original_task.created_at
    elif dated_tasks:
        reference_date = min(task.created_at for task in dated_tasks)
    else:
        return 1

    return min(5, ((reference_date.day - 1) // 7) + 1)


def _calculate_revision_points(task) -> Decimal:
    type_of_work = task.type_of_work
    if not type_of_work:
        return Decimal("0")

    if task.have_major_changes:
        return _to_decimal(type_of_work.major_changes_point)
    return _to_decimal(type_of_work.minor_changes_point)


def _calculate_negative_points(task) -> Decimal:
    return sum((_to_decimal(link.negative_remark.point) for link in task.negative_remark_links.all()), Decimal("0"))


def _to_decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _to_int(value) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0
