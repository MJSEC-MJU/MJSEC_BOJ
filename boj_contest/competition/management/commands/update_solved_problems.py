from django.core.management.base import BaseCommand
import requests
from competition.models import Participant, ContestProblem, Submission
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fetch solved problems and update the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user_id', type=str, required=True,
            help='User ID of the participant'
        )
        parser.add_argument(
            '--problem_id', type=int, required=True,
            help='Problem ID to be checked'
        )

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        problem_id = kwargs['problem_id']
        self.stdout.write(
            f"Checking solved status for user '{user_id}', problem {problem_id}"
        )

        # 참가자와 문제 조회
        try:
            participant = Participant.objects.get(user_id__username=user_id)
        except Participant.DoesNotExist:
            self.stderr.write(f"Participant '{user_id}' does not exist.")
            return

        try:
            problem = ContestProblem.objects.get(problem_id=problem_id)
        except ContestProblem.DoesNotExist:
            self.stderr.write(f"ContestProblem {problem_id} does not exist.")
            return

        # 이미 정답으로 기록된 Submission이 있으면 종료
        if Submission.objects.filter(
            user_id=participant,
            problem_id=problem,
            is_correct=True
        ).exists():
            self.stdout.write(
                f"{user_id} already solved problem {problem_id}."
            )
            return

        # solved.ac API 호출 함수
        def check_solved_ac(handle, pid):
            url = "https://solved.ac/api/v3/search/problem"
            params = {
                'query': f"solved_by:{handle} id:{pid}",
                'page': 1,
                'pageSize': 1,
            }
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stderr.write(f"Error calling solved.ac API: {e}")
                return False

            return data.get('count', 0) > 0

        solved = check_solved_ac(user_id, problem_id)

        # 동일 user/problem 중복 삭제: 최신 하나만 남김
        submissions_qs = Submission.objects.filter(
            user_id=participant,
            problem_id=problem
        )
        if submissions_qs.count() > 1:
            latest = submissions_qs.order_by('-submission_time').first()
            submissions_qs.exclude(pk=latest.pk).delete()

        # update_or_create로 중복 없이 삽입/갱신
        submission, created = Submission.objects.update_or_create(
            user_id=participant,
            problem_id=problem,
            defaults={
                'score': problem.points if solved else 0,
                'is_correct': solved,
                'submission_time': timezone.now(),
            }
        )

        status = 'correct' if solved else 'incorrect'
        self.stdout.write(
            f"Submission {submission.id} recorded as {status} "
            f"for user '{user_id}', problem {problem_id}."
        )
