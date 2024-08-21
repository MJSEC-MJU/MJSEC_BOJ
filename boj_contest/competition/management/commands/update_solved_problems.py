from django.core.management.base import BaseCommand
import requests
from competition.models import Participant, ContestProblem, Submission

class Command(BaseCommand):
    help = 'Fetch solved problems and update the database'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=str, help='User ID of the participant')
        parser.add_argument('--problem_id', type=int, help='Problem ID to be checked')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        problem_id = kwargs['problem_id']

        def is_problem_solved_by_user(user_id, problem_id):
            try:
                participant = Participant.objects.get(user_id__username=user_id)
                return Submission.objects.filter(user_id=participant, problem_id__problem_id=problem_id).exists()
            except Participant.DoesNotExist:
                self.stderr.write(f"Participant with User ID {user_id} does not exist.")
                return False

        def update_newly_solved_problems(user_id, problem_id):
            base_url = "https://solved.ac/api/v3/search/problem"
            summary_url = f"https://solved.ac/api/v3/user/show?handle={user_id}"

            try:
                response = requests.get(summary_url)
                response.raise_for_status()
                data = response.json()
                total_problems_solved = data.get('solvedCount', 0)
            except requests.RequestException as e:
                self.stderr.write(f"Failed to fetch data: {e}")
                return False

            page_size = 50
            if total_problems_solved == 0:
                return False
            else:
                max_page = (total_problems_solved + page_size - 1) // page_size
            low, high = 1, max_page

            while low <= high:
                mid = (low + high) // 2
                params = {
                    "query": f"solved_by:{user_id}",
                    "page": mid
                }
                try:
                    response = requests.get(base_url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    problems = data.get('items', [])
                except requests.RequestException as e:
                    self.stderr.write(f"Failed to fetch data: {e}")
                    return False

                if not problems:
                    high = mid - 1
                    continue

                # Convert problem IDs to integers for comparison
                try:
                    problem_ids = [int(p['problemId']) for p in problems]
                except ValueError as e:
                    self.stderr.write(f"Failed to convert problem IDs to integers: {e}")
                    return False

                if problem_ids:
                    min_problem_id = min(problem_ids)
                    max_problem_id = max(problem_ids)
                else:
                    self.stderr.write("No problems found in the response.")
                    return False

                if min_problem_id <= problem_id <= max_problem_id:
                    if problem_id in problem_ids:
                        return True
                    else:
                        return False
                elif problem_id < min_problem_id:
                    high = mid - 1
                else:
                    low = mid + 1

            return False

        if is_problem_solved_by_user(user_id, problem_id):
            self.stdout.write(f"User {user_id} has solved problem {problem_id}.")
        else:
            if update_newly_solved_problems(user_id, problem_id):
                self.stdout.write(f"User {user_id} has solved problem {problem_id}.")
            else:
                self.stdout.write(f"User {user_id} has not solved problem {problem_id}.")
