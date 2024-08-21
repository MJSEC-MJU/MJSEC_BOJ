from django.db import models
from django.utils import timezone
from feed.models import Feed
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
class Participant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class ContestProblem(models.Model):
    id = models.AutoField(primary_key=True)  # ID 필드를 명시적으로 추가합니다.
    problem_id = models.IntegerField(unique=True)
    points = models.IntegerField(default=1000)
    min_points = models.IntegerField(default=100)  # 최소 점수

    def __str__(self):
        return str(self.problem_id)
    def get_absolute_url(self):
        return reverse('feed:problem_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # 문제를 저장한 후 점수를 조정하고 피드를 추가합니다
        created = self.pk is None
        super().save(*args, **kwargs)
        self.update_problem_score()
        if created:
            self.create_feed_entry()

    def update_problem_score(self):
        # 현재 문제의 점수를 업데이트하는 로직
        solved_count = Submission.objects.filter(problem_id=self).values('user_id').distinct().count()
        # 전체 참가자 수를 계산합니다
        total_participants = Participant.objects.count()
        max_decrement_factor = 0.99
        if total_participants > 0:
            # 점수 감소 비율 계산
            if solved_count > 1:
                decrement_factor = min(max_decrement_factor, max_decrement_factor * (solved_count-1) / total_participants)
            else:
                decrement_factor = 0

            # 초기 점수에서 점수를 감소시킵니다
            initial_points = self.points
            new_points = initial_points * (1 - decrement_factor)
            new_points = max(new_points, self.min_points)  # 최소 점수 이하로 떨어지지 않도록 합니다
        else:
            new_points = self.points
        
        # 점수 업데이트 후 save() 호출 대신 직접 업데이트
        ContestProblem.objects.filter(pk=self.pk).update(points=new_points)

    def create_feed_entry(self):
        # 문제 생성 시 피드 항목을 추가합니다
        Feed.objects.create(
            title=f"Problem: {self.problem_id}",
            content=f"A new problem has been added: {self.problem_id}. It has {self.points} points.",
            problem=self
            
        )


class Submission(models.Model):
    user_id = models.ForeignKey(Participant, on_delete=models.CASCADE)
    problem_id = models.ForeignKey(ContestProblem, on_delete=models.CASCADE)
    submission_time = models.DateTimeField(default=timezone.now)
    score = models.FloatField(default=0)  # 점수 필드 추가

    def __str__(self):
        return f"{self.user_id} - {self.problem_id}"
    
