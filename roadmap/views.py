import logging

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.views import APIView

from .models import Category, Resource, TaskType
from .schema import NO_CONTENT, UNAUTHORIZED, conflict, id_parameter, not_found, validation_error
from .serializers import CategorySerializer, ResourceSerializer, TaskTypeSerializer

logger = logging.getLogger(__name__)


def invalid_data(serializer, request, label):
    """400 з помилками по полях. У лог — лише назви полів, без значень: там можуть бути чутливі дані."""
    logger.warning("Invalid %s data from user_id=%s: fields %s", label, request.user.id, sorted(serializer.errors))
    return Response(
        {"detail": "Invalid data.", "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )

# Приклади для документації категорій.
CATEGORY_REQUEST = OpenApiExample(
    "Категорія", value={"name": "Web", "description": "Вразливості вебзастосунків"}, request_only=True
)
CATEGORY_RESPONSE = {"id": 1, "name": "Web", "description": "Вразливості вебзастосунків"}
CATEGORY_VALIDATION_ERROR = validation_error(
    **{
        "Без назви": {"name": ["This field is required."]},
        "Назва вже існує": {"name": ["category with this name already exists."]},
        "Задовга назва": {"name": ["Ensure this field has no more than 100 characters."]},
    }
)


class CategoryListView(APIView):
    @extend_schema(
        tags=["Categories"],
        operation_id="categories_list",
        summary="Список усіх категорій",
        description="Доступно всім, токен не потрібен.",
        auth=[],
        responses={
            200: OpenApiResponse(
                CategorySerializer(many=True),
                examples=[OpenApiExample("Список", value=[CATEGORY_RESPONSE, {"id": 2, "name": "Crypto", "description": "Криптографія"}])],
            ),
        },
    )
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        logger.debug("Returned %d categories", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        tags=["Categories"],
        summary="Додати категорію",
        description="Лише для авторизованих користувачів. Назва унікальна, до 100 символів; опис необов'язковий.",
        request=CategorySerializer,
        examples=[CATEGORY_REQUEST],
        responses={
            201: OpenApiResponse(CategorySerializer, description="Категорію створено.", examples=[OpenApiExample("Створено", value=CATEGORY_RESPONSE)]),
            400: CATEGORY_VALIDATION_ERROR,
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "category")
        saved = serializer.save()
        logger.info("Category created: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    @extend_schema(
        tags=["Categories"],
        summary="Одна категорія",
        description="Доступно всім, токен не потрібен.",
        auth=[],
        parameters=[id_parameter("категорії")],
        responses={
            200: OpenApiResponse(CategorySerializer, examples=[OpenApiExample("Категорія", value=CATEGORY_RESPONSE)]),
            404: not_found("Category"),
        },
    )
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    @extend_schema(
        tags=["Categories"],
        summary="Редагувати категорію",
        description="Лише для авторизованих користувачів. Потрібно передати всі поля (повна заміна).",
        parameters=[id_parameter("категорії")],
        request=CategorySerializer,
        examples=[OpenApiExample("Новий опис", value={"name": "Web", "description": "Новий опис"}, request_only=True)],
        responses={
            200: OpenApiResponse(
                CategorySerializer,
                description="Категорію оновлено.",
                examples=[OpenApiExample("Оновлено", value={"id": 1, "name": "Web", "description": "Новий опис"})],
            ),
            400: CATEGORY_VALIDATION_ERROR,
            401: UNAUTHORIZED,
            404: not_found("Category"),
        },
    )
    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "category")
        saved = serializer.save()
        logger.info("Category updated: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data)

    @extend_schema(
        tags=["Categories"],
        summary="Видалити категорію",
        description="Лише для авторизованих користувачів. Категорію, в якій є типи завдань, видалити не можна: спершу видаліть їх.",
        parameters=[id_parameter("категорії")],
        responses={
            204: NO_CONTENT,
            401: UNAUTHORIZED,
            404: not_found("Category"),
            409: conflict(
                "У категорії є типи завдань.",
                "Cannot delete category: it has 3 task type(s). Delete them first.",
            ),
        },
    )
    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        try:
            category.delete()
        except ProtectedError as e:
            logger.warning(
                "Category delete refused: id=%s has %d task type(s) (user_id=%s)",
                pk, len(e.protected_objects), request.user.id,
            )
            return Response(
                {"detail": f"Cannot delete category: it has {len(e.protected_objects)} task type(s). Delete them first."},
                status=status.HTTP_409_CONFLICT,
            )
        logger.info("Category deleted: id=%s %r by user_id=%s", pk, str(category), request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryTaskTypesView(APIView):
    @extend_schema(
        tags=["Categories"],
        operation_id="categories_task_types_list",
        summary="Типи завдань однієї категорії",
        description="Доступно всім, токен не потрібен.",
        auth=[],
        parameters=[id_parameter("категорії")],
        responses={
            200: OpenApiResponse(
                TaskTypeSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Типи завдань",
                        value=[{"id": 1, "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит"}],
                    )
                ],
            ),
            404: not_found("Category"),
        },
    )
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = TaskTypeSerializer(category.task_types.all(), many=True)
        return Response(serializer.data)


class TaskTypeListView(APIView):
    @extend_schema(tags=["Task types"], summary="Список усіх типів завдань", auth=[], responses={200: TaskTypeSerializer(many=True)})
    def get(self, request):
        task_types = TaskType.objects.all()
        serializer = TaskTypeSerializer(task_types, many=True)
        logger.debug("Returned %d task types", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        tags=["Task types"],
        summary="Додати тип завдання в категорію",
        request=TaskTypeSerializer,
        responses={
            201: TaskTypeSerializer,
            400: validation_error(**{"Назва вже є в категорії": {"non_field_errors": ["The fields category, name must make a unique set."]}}),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = TaskTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "task type")
        saved = serializer.save()
        logger.info("Task type created: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskTypeDetailView(APIView):
    @extend_schema(
        tags=["Task types"],
        summary="Один тип завдання",
        auth=[],
        parameters=[id_parameter("типу завдання")],
        responses={200: TaskTypeSerializer, 404: not_found("TaskType")},
    )
    def get(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        serializer = TaskTypeSerializer(task_type)
        return Response(serializer.data)

    @extend_schema(
        tags=["Task types"],
        summary="Редагувати тип завдання",
        parameters=[id_parameter("типу завдання")],
        request=TaskTypeSerializer,
        responses={
            200: TaskTypeSerializer,
            400: validation_error(**{"Без назви": {"name": ["This field is required."]}}),
            401: UNAUTHORIZED,
            404: not_found("TaskType"),
        },
    )
    def put(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        serializer = TaskTypeSerializer(task_type, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "task type")
        saved = serializer.save()
        logger.info("Task type updated: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data)

    @extend_schema(
        tags=["Task types"],
        summary="Видалити тип завдання",
        parameters=[id_parameter("типу завдання")],
        responses={
            204: NO_CONTENT,
            401: UNAUTHORIZED,
            404: not_found("TaskType"),
            409: conflict(
                "До типу завдання прив'язані ресурси.",
                "Cannot delete task type: it has 2 resource(s). Delete them first.",
            ),
        },
    )
    def delete(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        try:
            task_type.delete()
        except ProtectedError as e:
            logger.warning(
                "Task type delete refused: id=%s has %d resource(s) (user_id=%s)",
                pk, len(e.protected_objects), request.user.id,
            )
            return Response(
                {"detail": f"Cannot delete task type: it has {len(e.protected_objects)} resource(s). Delete them first."},
                status=status.HTTP_409_CONFLICT,
            )
        logger.info("Task type deleted: id=%s %r by user_id=%s", pk, str(task_type), request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskTypeResourcesView(APIView):
    @extend_schema(
        tags=["Task types"],
        summary="Статті й відео до типу завдання",
        auth=[],
        parameters=[id_parameter("типу завдання")],
        responses={200: ResourceSerializer(many=True), 404: not_found("TaskType")},
    )
    def get(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        serializer = ResourceSerializer(task_type.resources.all(), many=True)
        return Response(serializer.data)


class ResourceListView(APIView):
    @extend_schema(tags=["Resources"], summary="Список усіх ресурсів", auth=[], responses={200: ResourceSerializer(many=True)})
    def get(self, request):
        resources = Resource.objects.all()
        serializer = ResourceSerializer(resources, many=True)
        logger.debug("Returned %d resources", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        tags=["Resources"],
        summary="Додати статтю чи відео до типу завдання",
        request=ResourceSerializer,
        responses={
            201: ResourceSerializer,
            400: validation_error(**{"Невалідні url і type": {"url": ["Enter a valid URL."], "type": ['"podcast" is not a valid choice.']}}),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = ResourceSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "resource")
        saved = serializer.save()
        logger.info("Resource created: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResourceDetailView(APIView):
    @extend_schema(
        tags=["Resources"],
        summary="Один ресурс",
        auth=[],
        parameters=[id_parameter("ресурсу")],
        responses={200: ResourceSerializer, 404: not_found("Resource")},
    )
    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        serializer = ResourceSerializer(resource)
        return Response(serializer.data)

    @extend_schema(
        tags=["Resources"],
        summary="Редагувати ресурс",
        parameters=[id_parameter("ресурсу")],
        request=ResourceSerializer,
        responses={
            200: ResourceSerializer,
            400: validation_error(**{"Невалідний url": {"url": ["Enter a valid URL."]}}),
            401: UNAUTHORIZED,
            404: not_found("Resource"),
        },
    )
    def put(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        serializer = ResourceSerializer(resource, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer, request, "resource")
        saved = serializer.save()
        logger.info("Resource updated: id=%s %r by user_id=%s", saved.id, str(saved), request.user.id)
        return Response(serializer.data)

    @extend_schema(
        tags=["Resources"],
        summary="Видалити ресурс",
        parameters=[id_parameter("ресурсу")],
        responses={204: NO_CONTENT, 401: UNAUTHORIZED, 404: not_found("Resource")},
    )
    def delete(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        resource.delete()
        logger.info("Resource deleted: id=%s %r by user_id=%s", pk, str(resource), request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
