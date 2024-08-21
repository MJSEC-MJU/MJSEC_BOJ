# competition/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Count, Sum, F, Max
from .models import Participant, ContestProblem, Submission
from django.core.management import call_command
from django.db import models
from django.core.management.base import BaseCommand
import subprocess
from django.contrib.auth.decorators import login_required
import requests
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
def redirect_based_on_login(request):
    if request.user.is_authenticated:
        return redirect(reverse('feed:index'))
    else:
        return redirect(reverse('user:login'))
@login_required
def index(request):
    return HttpResponse("Welcome to the Contest")
@login_required
def register_participant(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        Participant.objects.create(user_id=user_id)
        return HttpResponse(f"User {user_id} registered successfully!")
    return render(request, 'competition/register.html')


@login_required
def submit_solution(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        problem_id = request.POST.get('problem_id')

        if not user_id or not problem_id:
            messages.error(request, "User ID and Problem ID are required.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # User 객체를 가져옵니다
        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            messages.error(request, f"User with User ID {user_id} does not exist.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # Participant 객체를 가져옵니다
        try:
            participant = Participant.objects.get(user_id=user)
        except Participant.DoesNotExist:
            messages.error(request, f"Participant with User ID {user_id} does not exist.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # ContestProblem 객체를 가져옵니다
        try:
            problem = ContestProblem.objects.get(problem_id=problem_id)
        except ContestProblem.DoesNotExist:
            messages.error(request, f"Problem with Problem ID {problem_id} does not exist.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # Submission이 이미 존재하는지 확인합니다
        if Submission.objects.filter(user_id=participant, problem_id=problem).exists():
            messages.error(request, "You have already submitted a solution for this problem.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        try:
            # 서브프로세스를 실행합니다
            result = subprocess.run(
                ['python', 'manage.py', 'update_solved_problems', '--user_id', user_id, '--problem_id', str(problem_id)],
                capture_output=True,
                text=True
            )
            result_stdout = result.stdout
            result_stderr = result.stderr

            if result.returncode != 0:
                messages.error(request, f"Error occurred: {result_stderr}")
                return redirect('feed:problem_detail', problem_id=problem_id)

            if f"User {user_id} has solved problem {problem_id}." in result_stdout:
                # 새로운 제출을 생성합니다
                 # 문제의 점수를 업데이트합니다
                
                Submission.objects.create(user_id=participant, problem_id=problem)
                problem.update_problem_score()
                messages.success(request, f"Successfully submitted a solution for problem {problem_id}.")
            else:
                messages.error(request, f"User {user_id} has not solved problem {problem_id}.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        return redirect('feed:problem_detail', problem_id=problem_id)
    
    return redirect('feed:index')


@login_required
def contest_results(request):
    # 전체 순위 데이터를 생성합니다
    results = (
        Submission.objects
        .select_related('user_id')
        .values('user_id__user_id', 'user_id__user__username')
        .annotate(
            solved_count=Count('problem_id'),
            total_score=Sum(F('problem_id__points')),
            last_submission_time=Max('submission_time')
        )
        .order_by('-total_score', '-solved_count', 'last_submission_time')
    )

    ranked_results = []
    rank = 1
    for result in results:
        result['rank'] = rank
        ranked_results.append(result)
        rank += 1

    # AJAX 요청에 대한 JSON 응답
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        time_score_results = (
            Submission.objects
            .select_related('user_id')
            .values('user_id__user__username', 'submission_time', 'problem_id__points')
            .annotate(
                total_score=Sum(F('problem_id__points'))
            )
            .order_by('user_id', 'submission_time')
        )

        user_scores = {}
        for result in time_score_results:
            username = result['user_id__user__username']
            submission_time = result['submission_time']
            problem_points = result['total_score']

            if username not in user_scores:
                user_scores[username] = {'times': [], 'scores': []}

            # 누적 점수 계산
            if user_scores[username]['scores']:
                current_score = user_scores[username]['scores'][-1] + problem_points
            else:
                current_score = problem_points

            user_scores[username]['times'].append(submission_time.isoformat())
            user_scores[username]['scores'].append(current_score)

        # 상위 5명의 사용자만 선택합니다
        top_users = sorted(user_scores.keys(), key=lambda k: max(user_scores[k]['scores']), reverse=True)[:5]

        top_user_scores = {
            user: {
                'times': user_scores[user]['times'],
                'scores': user_scores[user]['scores']
            }
            for user in top_users
        }

        return JsonResponse({'results': top_user_scores})

    # 기본 템플릿 렌더링
    return render(request, 'competition/results.html', {'results': ranked_results})

@login_required
def update_problems(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        problem_id = request.POST.get('problem_id')
        
        if not user_id or not problem_id:
            return HttpResponseBadRequest("User ID and Problem ID are required.")
        
        # Call the management command to update solved problems
        try:
            call_command('update_solved_problems', user_id=user_id, problem_id=problem_id)
            return HttpResponse(f"User {user_id} has solved problem {problem_id}.")
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {str(e)}")
    return render(request, 'competition/update.html')
