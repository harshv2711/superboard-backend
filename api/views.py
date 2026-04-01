from django.contrib.auth import logout
from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Brand, Client, ClientAttachment, ClientMonthlyAmount, ClientOwner, Group, GroupMember, NegativeRemark, NegativeRemarkOnTask, ScopeOfWork, ServiceCategory, Task, TaskAttachment, TaskOnStage, TaskStage, TypeOfWork
from .permissions import (
    CanWriteTaskByRole,
    IsAuthenticatedAndCanManageNegativeRemarks,
    IsAuthenticatedAndSuperuserOnly,
    IsClientOwnerOrReadOnly,
    is_account_planner,
    is_art_director,
    is_designer,
    is_privileged_user,
    user_can_designer_update_task,
    user_can_fully_manage_task,
    user_can_manage_client,
)
from .serializers import (
    BrandSerializer,
    ChangePasswordSerializer,
    ClientSerializer,
    ClientAttachmentSerializer,
    ClientMonthlyAmountSerializer,
    ClientOwnerSerializer,
    DesignerKpiSummarySerializer,
    EmailAuthTokenSerializer,
    GroupMemberSerializer,
    GroupSerializer,
    NegativeRemarkSerializer,
    NegativeRemarkOnTaskSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ScopeOfWorkSerializer,
    ServiceCategorySerializer,
    TaskSerializer,
    TaskAttachmentSerializer,
    TaskOnStageSerializer,
    TaskStageSerializer,
    TypeOfWorkSerializer,
)
from .utils.designer_kpi import calculate_designer_monthly_kpi


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at", "updated_at"]
    ordering = ["name"]


class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all().select_related("group", "user")
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["group", "user"]
    search_fields = ["group__name", "user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["id", "group__name", "user__email", "created_at"]
    ordering = ["group__name", "user__email"]


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "description"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class TypeOfWorkViewSet(viewsets.ModelViewSet):
    queryset = TypeOfWork.objects.all()
    serializer_class = TypeOfWorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["work_type_name"]
    ordering_fields = ["id", "work_type_name", "point"]
    ordering = ["work_type_name"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {"detail": "This type of work cannot be deleted because it is already used by one or more tasks."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NegativeRemarkViewSet(viewsets.ModelViewSet):
    queryset = NegativeRemark.objects.all()
    serializer_class = NegativeRemarkSerializer
    permission_classes = [IsAuthenticatedAndCanManageNegativeRemarks]
    search_fields = ["remark_name", "description"]
    ordering_fields = ["id", "remark_name", "point", "created_at", "updated_at"]
    ordering = ["-created_at", "-id"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.task_links.exists():
            return Response(
                {"detail": "This negative remark cannot be deleted because it is already linked to one or more tasks."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class NegativeRemarkOnTaskViewSet(viewsets.ModelViewSet):
    queryset = NegativeRemarkOnTask.objects.all().select_related("task", "task__client", "negative_remark")
    serializer_class = NegativeRemarkOnTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["task", "negative_remark"]
    search_fields = ["task__task_name", "task__client__name", "negative_remark__remark_name", "negative_remark__description"]
    ordering_fields = ["id", "task", "negative_remark", "created_at", "updated_at"]
    ordering = ["-created_at", "-id"]


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAttachment.objects.all().select_related("task", "task__client")
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["task"]
    search_fields = ["task__task_name", "task__client__name", "file"]
    ordering_fields = ["id", "task", "created_at", "updated_at"]
    ordering = ["-created_at", "-id"]


class TaskStageViewSet(viewsets.ModelViewSet):
    queryset = TaskStage.objects.all()
    serializer_class = TaskStageSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at", "updated_at"]
    ordering = ["id"]


class TaskOnStageViewSet(viewsets.ModelViewSet):
    queryset = TaskOnStage.objects.all().select_related("task_stage", "task", "task__client", "task__designer", "task__type_of_work")
    serializer_class = TaskOnStageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["task_stage", "task"]
    search_fields = ["task_stage__name", "task__task_name", "task__client__name", "task__designer__email"]
    ordering_fields = ["id", "task_stage", "task", "created_at", "updated_at"]
    ordering = ["task_stage__name", "-created_at", "-id"]


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().prefetch_related("owners")
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsClientOwnerOrReadOnly]
    search_fields = ["name", "client_interface", "client_interface_contact_number"]
    ordering_fields = ["id", "name", "client_interface_contact_number", "created_at", "updated_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        owner_id = self.request.query_params.get("owner")
        if owner_id:
            qs = qs.filter(owners__user_id=owner_id)
        return qs.distinct()

    def perform_create(self, serializer):
        if not (is_account_planner(self.request.user) or is_privileged_user(self.request.user)):
            raise PermissionDenied("Only account planners can create clients.")

        with transaction.atomic():
            client = serializer.save()
            if is_account_planner(self.request.user):
                ClientOwner.objects.get_or_create(user=self.request.user, client=client)


class ClientAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ClientAttachment.objects.all().select_related("client")
    serializer_class = ClientAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["client"]
    search_fields = ["client__name", "file"]
    ordering_fields = ["id", "client", "created_at", "updated_at"]
    ordering = ["-created_at", "-id"]


class ClientMonthlyAmountViewSet(viewsets.ModelViewSet):
    queryset = ClientMonthlyAmount.objects.all().select_related("client")
    serializer_class = ClientMonthlyAmountSerializer
    permission_classes = [IsAuthenticatedAndSuperuserOnly]
    filterset_fields = ["client", "date"]
    search_fields = ["client__name"]
    ordering_fields = ["id", "client", "date", "amt", "created_at", "updated_at"]
    ordering = ["-date", "-id"]

    def perform_create(self, serializer):
        client = serializer.validated_data["client"]
        if not user_can_manage_client(self.request.user, client):
            raise PermissionDenied("You do not have permission to modify this client's monthly amount.")
        serializer.save()

    def perform_update(self, serializer):
        client = serializer.validated_data.get("client", serializer.instance.client)
        if not user_can_manage_client(self.request.user, client):
            raise PermissionDenied("You do not have permission to modify this client's monthly amount.")
        serializer.save()


class ClientOwnerViewSet(viewsets.ModelViewSet):
    queryset = ClientOwner.objects.all().select_related("user", "client")
    serializer_class = ClientOwnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["user", "client"]
    search_fields = ["user__email", "client__name"]
    ordering_fields = ["id", "created_at", "user__email", "client__name"]
    ordering = ["user__email", "client__name"]

    def perform_create(self, serializer):
        user = serializer.validated_data["user"]
        client = serializer.validated_data["client"]

        if is_privileged_user(self.request.user):
            serializer.save()
            return

        if (
            is_account_planner(self.request.user)
            and user.id == self.request.user.id
            and not client.owners.exists()
        ):
            serializer.save()
            return

        raise PermissionDenied("You do not have permission to change this client's ownership.")

    def perform_update(self, serializer):
        client = serializer.validated_data.get("client", serializer.instance.client)
        if not user_can_manage_client(self.request.user, client):
            raise PermissionDenied("You do not have permission to change this client's ownership.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_can_manage_client(self.request.user, instance.client):
            raise PermissionDenied("You do not have permission to change this client's ownership.")
        instance.delete()


class ScopeOfWorkViewSet(viewsets.ModelViewSet):
    queryset = ScopeOfWork.objects.all().select_related("client", "service_category").prefetch_related("type_of_work")
    serializer_class = ScopeOfWorkSerializer
    permission_classes = [permissions.IsAuthenticated, IsClientOwnerOrReadOnly]
    filterset_fields = ["client"]
    search_fields = ["deliverable_name", "description", "service_category__name"]
    ordering_fields = ["id", "client", "service_category", "service_category__name", "deliverable_name", "total_unit", "created_at", "updated_at"]
    ordering = ["client", "service_category__name", "deliverable_name"]

    def perform_create(self, serializer):
        client = serializer.validated_data["client"]
        if not user_can_manage_client(self.request.user, client):
            raise PermissionDenied("You do not have permission to modify this client's scope of work.")
        serializer.save()

    def perform_update(self, serializer):
        client = serializer.validated_data.get("client", serializer.instance.client)
        if not user_can_manage_client(self.request.user, client):
            raise PermissionDenied("You do not have permission to modify this client's scope of work.")
        serializer.save()


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related("client", "scope_of_work", "designer", "type_of_work", "created_by", "revision_of", "redo_of")
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, CanWriteTaskByRole]

    filterset_fields = ["client", "scope_of_work", "designer", "type_of_work", "revision_of", "redo_of"]
    search_fields = ["task_name", "instructions", "client__name"]
    ordering_fields = ["id", "target_date", "created_at", "updated_at"]
    ordering = ["-target_date", "-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_designer(self.request.user):
            qs = qs.filter(designer=self.request.user)
        return qs

    def _resolve_task_client(self, serializer):
        client = serializer.validated_data.get("client")
        if client is not None:
            return client

        scope_of_work = serializer.validated_data.get("scope_of_work")
        if scope_of_work is not None:
            return scope_of_work.client

        revision_of = serializer.validated_data.get("revision_of")
        if revision_of is not None:
            return revision_of.client

        redo_of = serializer.validated_data.get("redo_of")
        if redo_of is not None:
            return redo_of.client

        return serializer.instance.client if serializer.instance is not None else None

    def perform_create(self, serializer):
        client = self._resolve_task_client(serializer)
        if not (
            is_privileged_user(self.request.user)
            or is_art_director(self.request.user)
            or user_can_manage_client(self.request.user, client)
        ):
            raise PermissionDenied("You do not have permission to modify this client's tasks.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        task = serializer.instance
        if user_can_fully_manage_task(self.request.user, task):
            serializer.save()
            return

        if user_can_designer_update_task(self.request.user, task):
            allowed_fields = {"is_marked_completed_by_designer", "stage"}
            requested_fields = set(serializer.initial_data.keys())
            if not requested_fields.issubset(allowed_fields):
                raise PermissionDenied("Designers can only update their own completion flag or stage.")
            serializer.save()
            return

        raise PermissionDenied("You do not have permission to modify this task.")

    def perform_destroy(self, instance):
        if not user_can_fully_manage_task(self.request.user, instance):
            raise PermissionDenied("You do not have permission to delete this task.")
        try:
            instance.delete()
        except ProtectedError as exc:
            related_task = (
                instance.revisions.order_by("revision_no", "id").first()
                or instance.redos.order_by("redo_no", "id").first()
            )
            related_kind = "revision" if related_task and related_task.revision_of_id == instance.id else "redo"
            task_name = instance.task_name or f"Task #{instance.id}"

            if related_task:
                raise PermissionDenied(
                    f"Cannot delete the task because {task_name} is associated with another task ({related_kind})."
                ) from exc

            raise PermissionDenied(
                f"Cannot delete the task because {task_name} is associated with another task."
            ) from exc

    @action(detail=False, methods=["get"], url_path="designer-kpi")
    def designer_kpi(self, request):
        month_value = (request.query_params.get("month") or "").strip()
        if not month_value:
            raise ValidationError({"month": "Month is required in YYYY-MM format."})

        try:
            year, month = month_value.split("-", 1)
            year = int(year)
            month = int(month)
        except (AttributeError, TypeError, ValueError):
            raise ValidationError({"month": "Month must be in YYYY-MM format."})

        if month < 1 or month > 12:
            raise ValidationError({"month": "Month must be between 01 and 12."})

        designer_id_param = request.query_params.get("designer_id")
        if is_designer(request.user):
            designer_id = request.user.id
        elif designer_id_param:
            try:
                designer_id = int(designer_id_param)
            except (TypeError, ValueError):
                raise ValidationError({"designer_id": "Designer id must be a valid integer."})
        else:
            raise ValidationError({"designer_id": "Designer id is required."})

        kpi_summary = calculate_designer_monthly_kpi(designer_id=designer_id, year=year, month=month)
        payload = {
            "designer_id": designer_id,
            "month": f"{year:04d}-{month:02d}",
            "total_kpi_score": kpi_summary["total_kpi_score"],
            "weekly_scores": kpi_summary["weekly_scores"],
        }
        serializer = DesignerKpiSummarySerializer(payload)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def revisions(self, request, pk=None):
        """
        GET /api/tasks/{id}/revisions/
        Returns all revisions of this task.
        """
        task = self.get_object()
        qs = task.revisions.all().select_related("client", "designer", "type_of_work", "revision_of", "redo_of").order_by("revision_no", "id")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def redos(self, request, pk=None):
        """
        GET /api/tasks/{id}/redos/
        Returns all redos of this task.
        """
        task = self.get_object()
        qs = task.redos.all().select_related("client", "designer", "type_of_work", "revision_of", "redo_of").order_by("redo_no", "id")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def originals(self, request):
        """
        GET /api/tasks/originals/
        Returns tasks that are NOT revisions and NOT redos.
        """
        qs = self.get_queryset().filter(revision_of__isnull=True, redo_of__isnull=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def only_revisions(self, request):
        """
        GET /api/tasks/only_revisions/
        Returns tasks that ARE revisions.
        """
        qs = self.get_queryset().filter(revision_of__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def only_redos(self, request):
        """
        GET /api/tasks/only_redos/
        Returns tasks that ARE redos.
        """
        qs = self.get_queryset().filter(redo_of__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)


class LoginView(ObtainAuthToken):
    """
    POST /api/auth/login/
    body: {"email": "...", "password": "..."}
    """

    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.select_related("user").get(key=response.data["token"])
        return Response(
            {
                "token": token.key,
                "user_id": token.user_id,
                "email": token.user.email,
                "first_name": token.user.first_name,
                "last_name": token.user.last_name,
                "role": token.user.role,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(ProfileSerializer(request.user).data)

    def patch(self, request, *args, **kwargs):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
