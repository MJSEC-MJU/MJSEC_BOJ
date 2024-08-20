# competition/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Count, Sum, F
from .models import Participant, ContestProblem, Submission
from django.core.management import call_command
from django.db import models
from django.core.management.base import BaseCommand
import subprocess
import requests
from django.db import transaction
def index(request):
    return HttpResponse("Welcome to the Contest")

def register_participant(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        Participant.objects.create(user_id=user_id)
        return HttpResponse(f"User {user_id} registered successfully!")
    return render(request, 'competition/register.html')


def submit_solution(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        problem_id = request.POST.get('problem_id')

        if not user_id or not problem_id:
            return HttpResponseBadRequest("User ID and Problem ID are required.")

        try:
            user = Participant.objects.get(user_id=user_id)
        except Participant.DoesNotExist:
            return HttpResponseBadRequest(f"Participant with User ID {user_id} does not exist.")

        try:
            problem = ContestProblem.objects.get(problem_id=problem_id)
        except ContestProblem.DoesNotExist:
            return HttpResponseBadRequest(f"Problem with Problem ID {problem_id} does not exist.")

        if Submission.objects.filter(user_id=user, problem_id=problem).exists():
            return HttpResponse("You have already submitted a solution for this problem.")

        # Use subprocess to call the management command
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'update_solved_problems', '--user_id', user_id, '--problem_id', str(problem_id)],
                capture_output=True,
                text=True
            )
            result_stdout = result.stdout
            result_stderr = result.stderr

            if result.returncode != 0:
                return HttpResponseBadRequest(f"Error occurred: {result_stderr}")

            if f"User {user_id} has solved problem {problem_id}." in result_stdout:
                # 문제에 대한 제출을 기록합니다
                Submission.objects.create(user_id=user, problem_id=problem)
                
                # 점수 업데이트 로직 추가
                problem.save()

                return HttpResponse(f"User {user_id} has successfully submitted a solution for problem {problem_id}.")
            else:
                return HttpResponseBadRequest(f"User {user_id} has not solved problem {problem_id}.")
        except Exception as e:
            return HttpResponseBadRequest(f"An unexpected error occurred: {str(e)}")
    
    return render(request, 'competition/submit.html')


def contest_results(request):
    # 각 참가자의 해결한 문제 수 및 점수를 계산
    results = (
        Submission.objects
        .select_related('user_id')  # Participant 모델과 조인
        .values('user_id__user_id')
        .annotate(
            solved_count=Count('problem_id'),  # 해결한 문제의 수
            total_score=Sum(F('problem_id__points')),  # 총 점수, ContestProblem에 points 필드가 있다고 가정
        )
        .order_by('-total_score', '-solved_count')  # 점수 및 해결한 문제 수로 정렬
    )

    # 순위 계산
    ranked_results = []
    rank = 1
    for result in results:
        result['rank'] = rank
        ranked_results.append(result)
        rank += 1

    return render(request, 'competition/results.html', {'results': ranked_results})

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
