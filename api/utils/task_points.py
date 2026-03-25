from decimal import Decimal

from django.db.models import Max, Prefetch

from api.models import NegativeRemarkOnTask, Task


def calculate_task_points(task) -> float:
    if task.revision_of_id or task.redo_of_id:
        raise ValueError("calculate_task_points() accepts original tasks only.")

    optimized_task = _get_original_task_queryset().get(pk=task.pk)
    return _calculate_task_points_from_instance(optimized_task)


def calculate_designer_points(designer) -> float:
    tasks = _get_original_task_queryset().filter(
        designer=designer,
        revision_of__isnull=True,
        redo_of__isnull=True,
    )

    total = Decimal("0")
    for task in tasks:
        total += _calculate_task_points_from_instance(task)

    return float(total)


def _get_original_task_queryset():
    return (
        Task.objects.filter(revision_of__isnull=True, redo_of__isnull=True)
        .select_related("type_of_work")
        .annotate(
            max_revision_slides=Max("revisions__slides"),
            max_redo_slides=Max("redos__slides"),
        )
        .prefetch_related(
            Prefetch(
                "revisions",
                queryset=Task.objects.select_related("type_of_work").order_by("id"),
            ),
            Prefetch(
                "redos",
                queryset=_get_redo_queryset().order_by("id"),
            ),
            Prefetch(
                "negative_remark_links",
                queryset=NegativeRemarkOnTask.objects.select_related("negative_remark").order_by("id"),
            ),
        )
    )


def _get_redo_queryset():
    return (
        Task.objects.select_related("type_of_work")
        .annotate(max_revision_slides=Max("revisions__slides"))
        .prefetch_related(
            Prefetch(
                "revisions",
                queryset=Task.objects.select_related("type_of_work").order_by("id"),
            )
        )
    )


def _calculate_task_points_from_instance(task) -> Decimal:
    if not task.type_of_work_id:
        return Decimal("0")

    total = _calculate_original_points(task)
    total += _calculate_revision_points(task.revisions.all(), task.type_of_work)
    total += _calculate_redo_points(task.redos.all())
    total += _calculate_negative_remark_points(task)
    total += _calculate_excellence_points(task)
    return total


def _calculate_original_points(task) -> Decimal:
    highest_slides = _get_highest_slides(
        task.slides,
        task.max_revision_slides,
        task.max_redo_slides,
    )
    return _to_decimal(task.type_of_work.point) * Decimal(highest_slides)


def _calculate_revision_points(revisions, type_of_work) -> Decimal:
    total = Decimal("0")
    for revision in revisions:
        if revision.have_major_changes:
            total += _to_decimal(type_of_work.major_changes_point)
        if revision.have_minor_changes:
            total += _to_decimal(type_of_work.minor_changes_point)
    return total


def _calculate_redo_points(redos) -> Decimal:
    total = Decimal("0")
    for redo in redos:
        total += _calculate_redo_points_for_task(redo)
    return total


def _calculate_redo_points_for_task(redo_task) -> Decimal:
    total = Decimal("0")
    redo_type_of_work = redo_task.type_of_work

    if redo_type_of_work:
        highest_slides = _get_highest_slides(redo_task.slides, redo_task.max_revision_slides)
        total += _to_decimal(redo_type_of_work.redo_point) * Decimal(highest_slides)
        total += _calculate_revision_points(redo_task.revisions.all(), redo_type_of_work)

    return total


def _calculate_negative_remark_points(task) -> Decimal:
    total = Decimal("0")
    for negative_remark_link in task.negative_remark_links.all():
        total += negative_remark_link.negative_remark.point
    return total


def _calculate_excellence_points(task) -> Decimal:
    if task.excellence is None:
        return Decimal("0")
    return task.excellence


def _get_highest_slides(*slide_values) -> int:
    return max(value for value in slide_values if value is not None)


def _to_decimal(value) -> Decimal:
    return Decimal(str(value or 0))
