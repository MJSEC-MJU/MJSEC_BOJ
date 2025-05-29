# competition/management/commands/update_solved_problems.py
from django.core.management.base import BaseCommand
import requests
from competition.models import Participant, ContestProblem, Submission
from django.utils import timezone

class Command(BaseCommand):
    help = 'Fetch solved problems and update the database'

    def add_arguments(self, parser):
        parser.add_argument('--user_id',   type=str, required=True)
        parser.add_argument('--problem_id',type=int, required=True)

    def handle(self, *args, **kwargs):
        user_id    = kwargs['user_id']
        problem_id = kwargs['problem_id']

        try:
            participant = Participant.objects.get(user_id__username=user_id)
            problem     = ContestProblem.objects.get(problem_id=problem_id)
        except (Participant.DoesNotExist, ContestProblem.DoesNotExist):
            return

        # 이미 정답 처리된 적이 있으면 아무것도 안 함
        if Submission.objects.filter(user_id=participant,
                                     problem_id=problem,
                                     is_correct=True).exists():
            return

        # solved.ac API 호출
        def check_solved_ac(handle, pid):
            url    = "https://solved.ac/api/v3/search/problem"
            params = {
                'query': f"solved_by:{handle} id:{pid}",
                'page': 1, 'pageSize': 1,
            }
            try:
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                return r.json().get('count',0) > 0
            except:
                return False

        solved = check_solved_ac(user_id, problem_id)
        now    = timezone.now()

        if solved:
            # 정답이면 하나만 남기고 업데이트
            Submission.objects.update_or_create(
                user_id=participant,
                problem_id=problem,
                defaults={
                    'is_correct':     True,
                    'score':          problem.points,
                    'submission_time': now,
                }
            )
        else:
            # 오답이면 새 레코드 생성 → 페널티(지연) 로직에서 count를 셀 수 있음
            Submission.objects.create(
                user_id=participant,
                problem_id=problem,
                is_correct=False,
                score=0,
                submission_time=now,
            )
