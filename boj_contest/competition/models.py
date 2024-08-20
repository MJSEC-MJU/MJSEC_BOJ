from django.db import models
from django.utils import timezone

class Participant(models.Model):
    user_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.user_id

class ContestProblem(models.Model):
    id = models.AutoField(primary_key=True)  # ID 필드를 명시적으로 추가합니다.
    problem_id = models.IntegerField(unique=True)
    points = models.IntegerField(default=1000)
    min_points = models.IntegerField(default=100)  # 최소 점수

    def __str__(self):
        return str(self.problem_id)

    def save(self, *args, **kwargs):
        # 문제를 저장하기 전에 점수를 조정합니다
        if not self.pk:
            # 새 문제일 때만 점수를 업데이트
            super().save(*args, **kwargs)
            self.update_problem_score()
        else:
            super().save(*args, **kwargs)
            self.update_problem_score()

    def update_problem_score(self):
        # 현재 문제의 점수를 업데이트하는 로직
        solved_count = Submission.objects.filter(problem_id=self).values('user_id').distinct().count()

        if solved_count > 0:
            # 점수 감소 비율 설정
            decrement_factor = 0.05  # 점수 감소 비율 (예: 5%)

            # 점수 비례 감소
            score_decrease = self.points * (decrement_factor * solved_count)
            new_points = self.points - score_decrease
            
            # 최소 점수 설정
            if new_points < self.min_points:
                new_points = self.min_points
        else:
            new_points = self.points
        
        self.points = new_points

class Submission(models.Model):
    user_id = models.ForeignKey(Participant, on_delete=models.CASCADE)
    problem_id = models.ForeignKey(ContestProblem, on_delete=models.CASCADE)
    submission_time = models.DateTimeField(default=timezone.now)
    score = models.FloatField(default=0)  # 점수 필드 추가

    def __str__(self):
        return f"{self.user_id} - {self.problem_id}"
