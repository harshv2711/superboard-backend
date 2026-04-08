from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.functions import Lower
import re


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class TypeOfWork(models.Model):
    work_type_name = models.CharField(max_length=255, unique=True)
    point = models.FloatField(default=0.0)
    redo_point = models.FloatField(default=1.0)
    major_changes_point = models.FloatField(default=0.5)
    minor_changes_point = models.FloatField(default=0.25)

    class Meta:
        ordering = ["work_type_name"]
        indexes = [
            models.Index(fields=["work_type_name"]),
        ]

    def __str__(self):
        return self.work_type_name


class Client(models.Model):
    name = models.CharField(max_length=255)
    client_interface = models.CharField(max_length=255)
    client_interface_contact_number = models.CharField(max_length=20, blank=True, default="")
    logo = models.ImageField(upload_to="client_logos/", blank=True, null=True)
    accent_color = models.CharField(max_length=7, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_client_name_ci")
        ]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class ClientOwner(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_ownerships",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="owners",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__email", "client__name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "client"], name="uniq_client_owner_user_client")
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["client"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.client.name}"


class ClientMonthlyAmount(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="monthly_amounts",
    )
    date = models.DateField()
    amt = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["client", "date"], name="uniq_client_monthly_amount_client_date")
        ]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.client.name} | {self.date} | {self.amt}"


class AdditionalPoints(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="additional_points",
    )
    points = models.DecimalField(max_digits=12, decimal_places=4)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.user.email} | {self.date} | {self.points}"


class Group(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["group__name", "user__email"]
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="uniq_group_member_group_user")
        ]
        indexes = [
            models.Index(fields=["group"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.group.name} -> {self.user.email}"


class ClientAttachment(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="client_attachments/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Attachment #{self.id} for Client #{self.client_id}"


class ScopeOfWork(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="scope_of_work_items",
    )
    service_category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="scope_of_work_items",
    )
    type_of_work = models.ManyToManyField(
        TypeOfWork,
        related_name="scope_of_work_items",
        blank=True,
    )
    deliverable_name = models.CharField(max_length=150, blank=True, default="")
    description = models.TextField(blank=True, default="")
    total_unit = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client__name", "service_category__name", "deliverable_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "service_category"],
                name="uniq_scope_of_work_client_service_category",
            )
        ]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["service_category"]),
            models.Index(fields=["deliverable_name"]),
        ]

    def __str__(self):
        label = self.service_category_display or f"Scope #{self.pk}"
        return f"{self.client.name} | {label}"

    @property
    def service_category_display(self):
        if not self.service_category_id:
            return ""
        return self.service_category.name


class NegativeRemark(models.Model):
    remark_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    point = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["remark_name"]),
            models.Index(fields=["point"]),
        ]

    def __str__(self):
        return self.remark_name


class NegativeRemarkOnTask(models.Model):
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        related_name="negative_remark_links",
    )
    negative_remark = models.ForeignKey(
        NegativeRemark,
        on_delete=models.CASCADE,
        related_name="task_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "negative_remark"],
                name="uniq_negative_remark_on_task",
            )
        ]
        indexes = [
            models.Index(fields=["task"]),
            models.Index(fields=["negative_remark"]),
        ]

    def __str__(self):
        return f"Task #{self.task_id} -> {self.negative_remark.remark_name}"


class TaskAttachment(models.Model):
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="task_attachments/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["task"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Attachment #{self.id} for Task #{self.task_id}"


class TaskStage(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Stage(models.TextChoices):
        BACKLOG = "backlog", "Initiate"
        ON_GOING = "on_going", "Ongoing"
        COMPLETE = "complete", "Complete"
        APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL = (
            "approved_by_art_director_waiting_for_approval",
            "Approved By Art Director",
        )
        APPROVED = "approved", "Approved by Client"

    class RevisionType(models.TextChoices):
        SMALL = "small", "Small"
        MEDIUM = "medium", "Medium"
        LARGE = "large", "Large"

    class PromotionType(models.TextChoices):
        ORGANIC = "organic", "Organic"
        SPONSORED = "sponsored", "Sponsored"

    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        LINKEDIN = "linkedin", "LinkedIn"
        X = "x", "X"
        YOUTUBE = "youtube", "YouTube"
        TIKTOK = "tiktok", "TikTok"
        PINTEREST = "pinterest", "Pinterest"
        SNAPCHAT = "snapchat", "Snapchat"
        THREADS = "threads", "Threads"
        WHATSAPP = "whatsapp", "WhatsApp"

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="tasks",
        null=True,
        blank=True,
    )
    scope_of_work = models.ForeignKey(
        ScopeOfWork,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )

    revision_of = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="revisions",
    )

    redo_of = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="redos",
    )

    # Revision number per original task (only for revision tasks)
    revision_no = models.PositiveIntegerField(null=True, blank=True)
    redo_no = models.PositiveIntegerField(null=True, blank=True)

    task_name = models.CharField(max_length=255, blank=True)
    instructions = models.TextField(blank=True)
    InstructionsByArtDirector = models.TextField(blank=True, null=True)
    revision_type = models.CharField(
        max_length=10,
        choices=RevisionType.choices,
        blank=True,
        default="",
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    stage = models.CharField(
        max_length=64,
        choices=Stage.choices,
        default=Stage.BACKLOG,
    )

    designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="design_tasks",
    )

    type_of_work = models.ForeignKey(
        TypeOfWork,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tasks",
    )
    platform = models.CharField(
        max_length=32,
        choices=Platform.choices,
        blank=True,
        default="",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )

    target_date = models.DateField(null=True, blank=True)
    slides = models.PositiveIntegerField(default=1)
    impressions = models.PositiveIntegerField(null=True, blank=True)
    ctr = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    engagement_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    promotion_type = models.CharField(
        max_length=16,
        choices=PromotionType.choices,
        default=PromotionType.ORGANIC,
    )
    have_major_changes = models.BooleanField(default=False)
    have_minor_changes = models.BooleanField(default=False)

    # Originals: total revisions under them
    # Revisions: their own revision number (1/2/3...)
    revision_count = models.PositiveIntegerField(default=0)
    redo_count = models.PositiveIntegerField(default=0)

    excellence = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    excellence_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-target_date", "-created_at"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["designer"]),
            models.Index(fields=["type_of_work"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["scope_of_work"]),
            models.Index(fields=["target_date"]),
            models.Index(fields=["revision_of"]),
            models.Index(fields=["revision_no"]),
            models.Index(fields=["redo_of"]),
            models.Index(fields=["redo_no"]),
        ]

    @classmethod
    def normalize_stage(cls, stage):
        valid_stages = {choice for choice, _label in cls.Stage.choices}
        return stage if stage in valid_stages else cls.Stage.BACKLOG

    @classmethod
    def completion_state_for_stage(cls, stage):
        normalized_stage = cls.normalize_stage(stage)
        return {
            "is_marked_completed_by_superadmin": normalized_stage == cls.Stage.APPROVED,
            "is_marked_completed_by_account_planner": normalized_stage == cls.Stage.APPROVED,
            "is_marked_completed_by_art_director": normalized_stage in {
                cls.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                cls.Stage.APPROVED,
            },
            "is_marked_completed_by_designer": normalized_stage in {
                cls.Stage.COMPLETE,
                cls.Stage.APPROVED_BY_ART_DIRECTOR_WAITING_FOR_APPROVAL,
                cls.Stage.APPROVED,
            },
        }

    def clean(self):
        super().clean()
        self.stage = self.normalize_stage(self.stage)
        if self.pk and self.revision_of_id == self.pk:
            raise ValidationError({"revision_of": "A task cannot be a revision of itself."})
        if self.pk and self.redo_of_id == self.pk:
            raise ValidationError({"redo_of": "A task cannot be a redo of itself."})

        if self.revision_of_id and self.redo_of_id:
            raise ValidationError("A task cannot be both a revision and a redo.")

        if not self.revision_of_id and not self.redo_of_id and not self.client_id:
            raise ValidationError({"client": "Client is required for standalone tasks."})

        if not self.revision_of_id and not self.redo_of_id and not (self.task_name or "").strip():
            raise ValidationError({"task_name": "Task name is required for standalone tasks."})

        if self.revision_of_id and self.client_id:
            if self.revision_of.client_id != self.client_id:
                raise ValidationError(
                    {"revision_of": "Revision task must belong to the same client as the original task."}
                )
        if self.redo_of_id and self.client_id:
            if self.redo_of.client_id != self.client_id:
                raise ValidationError(
                    {"redo_of": "Redo task must belong to the same client as the original task."}
                )

        if self.scope_of_work_id:
            if self.client_id and self.scope_of_work.client_id != self.client_id:
                raise ValidationError(
                    {"scope_of_work": "Selected scope of work must belong to the same client as the task."}
                )

        if self.have_major_changes and self.have_minor_changes:
            raise ValidationError(
                {
                    "have_major_changes": "Major changes and minor changes cannot both be selected.",
                    "have_minor_changes": "Major changes and minor changes cannot both be selected.",
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def _sync_original_child_count(self, original_id: int, relation_field: str, count_field: str):
        count = Task.objects.filter(**{f"{relation_field}_id": original_id}).count()
        Task.objects.filter(id=original_id).update(**{count_field: count})

    def _prepare_numbered_child_task(
        self,
        *,
        relation_attr: str,
        number_attr: str,
        count_attr: str,
        prefix: str,
    ):
        relation_id = getattr(self, f"{relation_attr}_id")
        if not relation_id:
            return

        parent_task = getattr(self, relation_attr)
        if not self.client_id:
            self.client = parent_task.client

        base_name = (self.task_name or "").strip()
        if not base_name:
            base_name = (parent_task.task_name or "").strip() or "Untitled Task"

        base_name = re.sub(r"^(Revision|Redo)(\s+\d+)?\s*:\s*", "", base_name, flags=re.IGNORECASE).strip()

        with transaction.atomic():
            original = Task.objects.select_for_update().get(pk=relation_id)
            current_number = getattr(self, number_attr)
            if current_number is None:
                parent_number = getattr(parent_task, number_attr)
                if parent_number is not None:
                    current_number = parent_number + 1
                else:
                    last_no = (
                        Task.objects.filter(**{relation_attr: original})
                        .exclude(**{f"{number_attr}__isnull": True})
                        .aggregate(models.Max(number_attr))
                        .get(f"{number_attr}__max")
                        or 0
                    )
                    current_number = last_no + 1
                setattr(self, number_attr, current_number)

            setattr(self, count_attr, current_number)
            self.task_name = f"{prefix} {current_number}: {base_name}"

    def save(self, *args, **kwargs):
        old_revision_of_id = None
        old_redo_of_id = None
        if self.pk:
            old_revision_of_id = (
                Task.objects.filter(pk=self.pk)
                .values_list("revision_of_id", flat=True)
                .first()
            )
            old_redo_of_id = (
                Task.objects.filter(pk=self.pk)
                .values_list("redo_of_id", flat=True)
                .first()
            )

        if self.scope_of_work_id and not self.client_id:
            self.client = self.scope_of_work.client

        if self.revision_of_id:
            self._prepare_numbered_child_task(
                relation_attr="revision_of",
                number_attr="revision_no",
                count_attr="revision_count",
                prefix="Revision",
            )
        elif self.redo_of_id:
            self._prepare_numbered_child_task(
                relation_attr="redo_of",
                number_attr="redo_no",
                count_attr="redo_count",
                prefix="Redo",
            )

        self.full_clean()
        super().save(*args, **kwargs)

        if self.revision_of_id:
            self._sync_original_child_count(self.revision_of_id, "revision_of", "revision_count")
        if self.redo_of_id:
            self._sync_original_child_count(self.redo_of_id, "redo_of", "redo_count")

        if old_revision_of_id and old_revision_of_id != self.revision_of_id:
            self._sync_original_child_count(old_revision_of_id, "revision_of", "revision_count")
        if old_redo_of_id and old_redo_of_id != self.redo_of_id:
            self._sync_original_child_count(old_redo_of_id, "redo_of", "redo_count")

    def delete(self, *args, **kwargs):
        original_id = self.revision_of_id
        redo_original_id = self.redo_of_id
        super().delete(*args, **kwargs)

        if original_id:
            self._sync_original_child_count(original_id, "revision_of", "revision_count")
        if redo_original_id:
            self._sync_original_child_count(redo_original_id, "redo_of", "redo_count")

    def __str__(self):
        return f"#{self.id} | {self.client.name} | {self.task_name}"


class TaskOnStage(models.Model):
    task_stage = models.ForeignKey(
        TaskStage,
        on_delete=models.CASCADE,
        related_name="task_links",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="stage_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["task"], name="uniq_task_on_stage_task")
        ]
        indexes = [
            models.Index(fields=["task_stage"]),
            models.Index(fields=["task"]),
        ]

    def __str__(self):
        return f"{self.task_stage.name} -> Task #{self.task_id}"
