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
    logger.warning("Invalid %s data from user_id=%s: fields %s", label, request.user.id, sorted(serializer.errors))
    return Response(
        {"detail": "Invalid data.", "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


CATEGORY_REQUEST = OpenApiExample(
    "Category", value={"name": "Web", "description": "Web vulnerabilities"}, request_only=True
)
CATEGORY_RESPONSE = {"id": 1, "name": "Web", "description": "Web vulnerabilities"}
CATEGORY_VALIDATION_ERROR = validation_error(
    **{
        "Missing name": {"name": ["This field is required."]},
        "Duplicate name": {"name": ["category with this name already exists."]},
        "Name too long": {"name": ["Ensure this field has no more than 100 characters."]},
    }
)


class CategoryListView(APIView):
    @extend_schema(
        tags=["Categories"],
        operation_id="categories_list",
        summary="List categories",
        auth=[],
        responses={
            200: OpenApiResponse(
                CategorySerializer(many=True),
                examples=[OpenApiExample("List", value=[CATEGORY_RESPONSE, {"id": 2, "name": "Crypto", "description": "Cryptography"}])],
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
        summary="Create category",
        request=CategorySerializer,
        examples=[CATEGORY_REQUEST],
        responses={
            201: OpenApiResponse(CategorySerializer, examples=[OpenApiExample("Created", value=CATEGORY_RESPONSE)]),
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
        summary="Get category",
        auth=[],
        parameters=[id_parameter("Category")],
        responses={
            200: OpenApiResponse(CategorySerializer, examples=[OpenApiExample("Category", value=CATEGORY_RESPONSE)]),
            404: not_found("Category"),
        },
    )
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    @extend_schema(
        tags=["Categories"],
        summary="Update category",
        parameters=[id_parameter("Category")],
        request=CategorySerializer,
        examples=[OpenApiExample("New description", value={"name": "Web", "description": "New description"}, request_only=True)],
        responses={
            200: OpenApiResponse(
                CategorySerializer,
                examples=[OpenApiExample("Updated", value={"id": 1, "name": "Web", "description": "New description"})],
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
        summary="Delete category",
        parameters=[id_parameter("Category")],
        responses={
            204: NO_CONTENT,
            401: UNAUTHORIZED,
            404: not_found("Category"),
            409: conflict(
                "Category has task types.",
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
        summary="List category task types",
        auth=[],
        parameters=[id_parameter("Category")],
        responses={
            200: OpenApiResponse(
                TaskTypeSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Task types",
                        value=[{"id": 1, "category": 1, "name": "SQL Injection", "description": "SQL code injection"}],
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
    @extend_schema(tags=["Task types"], summary="List task types", auth=[], responses={200: TaskTypeSerializer(many=True)})
    def get(self, request):
        task_types = TaskType.objects.all()
        serializer = TaskTypeSerializer(task_types, many=True)
        logger.debug("Returned %d task types", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        tags=["Task types"],
        summary="Create task type",
        request=TaskTypeSerializer,
        responses={
            201: TaskTypeSerializer,
            400: validation_error(**{"Duplicate name in category": {"non_field_errors": ["The fields category, name must make a unique set."]}}),
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
        summary="Get task type",
        auth=[],
        parameters=[id_parameter("Task type")],
        responses={200: TaskTypeSerializer, 404: not_found("TaskType")},
    )
    def get(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        serializer = TaskTypeSerializer(task_type)
        return Response(serializer.data)

    @extend_schema(
        tags=["Task types"],
        summary="Update task type",
        parameters=[id_parameter("Task type")],
        request=TaskTypeSerializer,
        responses={
            200: TaskTypeSerializer,
            400: validation_error(**{"Missing name": {"name": ["This field is required."]}}),
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
        summary="Delete task type",
        parameters=[id_parameter("Task type")],
        responses={
            204: NO_CONTENT,
            401: UNAUTHORIZED,
            404: not_found("TaskType"),
            409: conflict(
                "Task type has resources.",
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
        summary="List task type resources",
        auth=[],
        parameters=[id_parameter("Task type")],
        responses={200: ResourceSerializer(many=True), 404: not_found("TaskType")},
    )
    def get(self, request, pk):
        task_type = get_object_or_404(TaskType, pk=pk)
        serializer = ResourceSerializer(task_type.resources.all(), many=True)
        return Response(serializer.data)


class ResourceListView(APIView):
    @extend_schema(tags=["Resources"], summary="List resources", auth=[], responses={200: ResourceSerializer(many=True)})
    def get(self, request):
        resources = Resource.objects.all()
        serializer = ResourceSerializer(resources, many=True)
        logger.debug("Returned %d resources", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        tags=["Resources"],
        summary="Create resource",
        request=ResourceSerializer,
        responses={
            201: ResourceSerializer,
            400: validation_error(**{"Invalid url and type": {"url": ["Enter a valid URL."], "type": ['"podcast" is not a valid choice.']}}),
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
        summary="Get resource",
        auth=[],
        parameters=[id_parameter("Resource")],
        responses={200: ResourceSerializer, 404: not_found("Resource")},
    )
    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        serializer = ResourceSerializer(resource)
        return Response(serializer.data)

    @extend_schema(
        tags=["Resources"],
        summary="Update resource",
        parameters=[id_parameter("Resource")],
        request=ResourceSerializer,
        responses={
            200: ResourceSerializer,
            400: validation_error(**{"Invalid url": {"url": ["Enter a valid URL."]}}),
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
        summary="Delete resource",
        parameters=[id_parameter("Resource")],
        responses={204: NO_CONTENT, 401: UNAUTHORIZED, 404: not_found("Resource")},
    )
    def delete(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        resource.delete()
        logger.info("Resource deleted: id=%s %r by user_id=%s", pk, str(resource), request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
