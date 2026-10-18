from django.urls import path
from . import views
urlpatterns = [
    path("categories", views.CategoryListView.as_view()),
    path("categories/<int:pk>", views.CategoryDetailView.as_view()),
    path("categories/<int:pk>/task-types", views.CategoryTaskTypesView.as_view()),
    path("task-types", views.TaskTypeListView.as_view()),
    path("task-types/<int:pk>", views.TaskTypeDetailView.as_view()),
    path("task-types/<int:pk>/resources", views.TaskTypeResourcesView.as_view()),
    path("resources", views.ResourceListView.as_view()),
    path("resources/<int:pk>", views.ResourceDetailView.as_view()),
]
