# competition/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import Count, Sum, Max, Q, Min
from django.db import models
from .models import Participant, ContestProblem, Submission
from django.core.management import call_command
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from datetime import datetime
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
            messages.error(request, "User ID와 Problem ID는 필수입니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # User 객체 가져오기
        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            messages.error(request, f"User ID {user_id}인 사용자가 존재하지 않습니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # Participant 객체 가져오기
        try:
            participant = Participant.objects.get(user_id=user)
        except Participant.DoesNotExist:
            messages.error(request, f"User ID {user_id}인 참가자가 존재하지 않습니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # ContestProblem 객체 가져오기
        try:
            problem = ContestProblem.objects.get(problem_id=problem_id)
        except ContestProblem.DoesNotExist:
            messages.error(request, f"Problem ID {problem_id}인 문제가 존재하지 않습니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # 문제_id를 정수로 변환
        try:
            problem_id = int(problem_id)
        except ValueError:
            messages.error(request, "문제 ID는 정수여야 합니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # 유효성 검증
        if problem_id <= 0:
            messages.error(request, "유효하지 않은 문제 ID입니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        if not user_id.isalnum():
            messages.error(request, "유효하지 않은 사용자 ID입니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # 이미 문제를 해결한 경우
        already_solved = Submission.objects.filter(
            user_id=participant,
            problem_id=problem,
            is_correct=True
        ).exists()

        if already_solved:
            messages.info(request, "이미 이 문제를 해결하셨습니다.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # 설정 파일에서 상수 불러오기
        MAX_FAILED_ATTEMPTS = getattr(settings, 'MAX_FAILED_ATTEMPTS', 3)
        DELAY_SECONDS = getattr(settings, 'DELAY_SECONDS', 30)

        now = timezone.now()
        delay_threshold_time = now - timedelta(seconds=DELAY_SECONDS)

        # 최근 실패한 제출 수 조회 (딜레이 기간 내)
        failed_submissions = Submission.objects.filter(
            user_id=participant,
            problem_id=problem,
            is_correct=False,
            submission_time__gte=delay_threshold_time
        ).count()

        if failed_submissions >= MAX_FAILED_ATTEMPTS:
            # 마지막 실패한 제출 시간 조회
            last_failed_submission = Submission.objects.filter(
                user_id=participant,
                problem_id=problem,
                is_correct=False
            ).order_by('-submission_time').first()

            if last_failed_submission:
                time_since_last_failed = (now - last_failed_submission.submission_time).total_seconds()
                if time_since_last_failed < DELAY_SECONDS:
                    wait_time = int(DELAY_SECONDS - time_since_last_failed)
                    messages.error(
                        request,
                        f"틀린 제출이 {MAX_FAILED_ATTEMPTS}번 이상 발생했습니다. {wait_time}초 후에 다시 시도해주세요."
                    )
                    return redirect('feed:problem_detail', problem_id=problem_id)

        # 동시 제출 방지 - 이미 제출 처리 중인 경우 확인
        cache_key = f"submit_solution_lock_{user_id}_{problem_id}"
        if cache.get(cache_key):
            messages.error(request, "현재 제출이 처리 중입니다. 잠시 후 다시 시도해주세요.")
            return redirect('feed:problem_detail', problem_id=problem_id)

        # 캐시에 잠금 설정 (제출 중 표시)
        cache.set(cache_key, True, timeout=60)  # 60초 동안 잠금 유지

        try:
            # 관리 명령어를 직접 호출하여 문제 해결 여부 업데이트
            call_command('update_solved_problems', user_id=user_id, problem_id=problem_id)
            
            # 최신 Submission 객체 가져오기
            submission = Submission.objects.filter(user_id=participant, problem_id=problem).order_by('-submission_time').first()

            if submission and submission.is_correct:
                messages.success(request, f"Problem {problem_id}에 대한 제출이 성공적으로 처리되었습니다.")
                problem.update_problem_score()
            else:
                # 실패한 제출인 경우, Submission 객체를 생성하여 실패 기록
                Submission.objects.create(
                    user_id=participant,
                    problem_id=problem,
                    score=0,
                    is_correct=False
                )
                messages.error(request, f"Problem {problem_id}에 대한 제출이 틀렸습니다.")
        except Exception as e:
            messages.error(request, f"예상치 못한 오류 발생: {str(e)}")
        finally:
            # 캐시에서 잠금 해제
            cache.delete(cache_key)

        return redirect('feed:problem_detail', problem_id=problem_id)

    return redirect('feed:index')

@login_required
def contest_results(request):
    # 전체 순위 데이터를 생성합니다
    results = (
        Submission.objects
        .select_related('user_id__user')  # user 관련 정보 미리 로드
        .filter(is_correct=True)  # 맞춘 제출만 필터링
        .values('user_id__user__username')
        .annotate(
            solved_count=Count('problem_id', distinct=True),
            total_score=Sum('problem_id__points'),
            last_submission_time=Min('submission_time', filter=Q(is_correct=True))
        )
        .order_by('-total_score', 'last_submission_time')  # 점수 내림차순, 마지막 성공 제출 시간 오름차순
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
            .select_related('user_id__user')
            .filter(is_correct=True)
            .values('user_id__user__username', 'submission_time', 'problem_id__points')
            .annotate(
                total_score=Sum('problem_id__points')
            )
            .order_by('user_id', 'submission_time')
        )

        user_scores = {}
        for result in time_score_results:
            username = result['user_id__user__username']
            submission_time = result['submission_time']
            problem_points = result['problem_id__points']

            if username not in user_scores:
                user_scores[username] = {'times': [], 'scores': []}

            # 누적 점수 계산
            if user_scores[username]['scores']:
                current_score = user_scores[username]['scores'][-1] + problem_points
            else:
                current_score = problem_points

            user_scores[username]['times'].append(submission_time)
            user_scores[username]['scores'].append(current_score)

        
        top_users = sorted(user_scores.keys(), key=lambda k: (max(user_scores[k]['scores']), -min(user_scores[k]['times']).timestamp()), reverse=True)[:]

        top_user_scores = {
            user: {
                'times': [time.isoformat() for time in user_scores[user]['times']],
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
            return HttpResponseBadRequest("User ID와 Problem ID는 필수입니다.")
        
        # 문제_id를 정수로 변환
        try:
            problem_id = int(problem_id)
        except ValueError:
            return HttpResponseBadRequest("문제 ID는 정수여야 합니다.")
        
        # 유효성 검증
        if problem_id <= 0:
            return HttpResponseBadRequest("유효하지 않은 문제 ID입니다.")
        
        if not user_id.isalnum():
            return HttpResponseBadRequest("유효하지 않은 사용자 ID입니다.")

        # 관리 명령어 호출하여 문제 해결 상태 업데이트
        try:
            call_command('update_solved_problems', user_id=user_id, problem_id=problem_id)
            return HttpResponse(f"User {user_id}가 Problem {problem_id}을(를) 해결했습니다.")
        except Exception as e:
            return HttpResponseBadRequest(f"오류: {str(e)}")
    return render(request, 'competition/update.html')
