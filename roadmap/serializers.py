from rest_framework import serializers

from .models import Category, Resource, TaskType


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType   
        fields = ["id", "category", "name", "description"]


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "task_type", "title", "url", "type"]
