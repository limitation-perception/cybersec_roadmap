from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TaskType(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="task_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ["category", "name"]
    

    def __str__(self):
        return self.name


class Resource(models.Model):
    TYPE_CHOICES = [
        ("article", "Article"),
        ("video", "Video"),
    ]

    task_type = models.ForeignKey(TaskType, on_delete=models.PROTECT, related_name="resources")
    title = models.CharField(max_length=200)
    url = models.URLField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return self.title
