from django.db import models
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
class Feed(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    problem = models.ForeignKey('competition.ContestProblem', on_delete=models.CASCADE, related_name='feeds', default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feeds')
    def __str__(self):
        return self.title