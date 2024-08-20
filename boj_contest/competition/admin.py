# competition/admin.py
from django.contrib import admin
from .models import Participant, ContestProblem, Submission

admin.site.register(Participant)
admin.site.register(ContestProblem)
admin.site.register(Submission)
