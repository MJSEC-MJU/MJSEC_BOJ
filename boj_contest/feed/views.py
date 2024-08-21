from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Feed 
from competition.models import Submission,Participant,ContestProblem
from django.http import HttpResponseBadRequest
@login_required
def feed_view(request):
    # 피드 항목을 생성일 내림차순으로 가져옵니다
    feed_items = Feed.objects.order_by('-created_at')

    # 현재 로그인한 사용자의 Participant 인스턴스를 가져옵니다
    try:
        participant = get_object_or_404(Participant, user_id=request.user)
    except Participant.DoesNotExist:
        participant = None

    # 로그인한 사용자가 문제를 해결했는지 확인합니다
    if participant:
        solved_problem_ids = set(
            Submission.objects.filter(user_id=participant).values_list('problem_id', flat=True)
        )
        # 피드 항목을 수정하여 문제 해결 여부를 포함합니다
        for item in feed_items:
            item.is_solved = item.problem.id in solved_problem_ids
            item.solved_count = Submission.objects.filter(problem_id=item.problem).count()
    else:
        # 인증되지 않은 경우 기본적으로 해결된 문제를 설정하지 않습니다
        for item in feed_items:
            item.is_solved = False
            item.solved_count = Submission.objects.filter(problem_id=item.problem).count()

    return render(request, 'feed/feed.html', {'feed_items': feed_items})
@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(ContestProblem, problem_id=problem_id)
    solved_count = Submission.objects.filter(problem_id=problem).count()
    return render(request, 'contest/problem_detail.html', {'problem': problem, 'solved_count': solved_count})
@login_required
def submit_solution(request, pk):
    if request.method == 'POST':
        problem = get_object_or_404(ContestProblem, pk=pk)
        user = request.user  # 로그인된 사용자

        # 로그인된 사용자를 Participant 객체로 변환
        try:
            participant = Participant.objects.get(user_id=user.username)
        except Participant.DoesNotExist:
            return HttpResponseBadRequest("Participant with the given user does not exist.")

        # 제출 기록을 생성
        Submission.objects.create(user_id=participant, problem_id=problem, score=problem.points)
        
        # 제출 성공 후 피드로 리디렉션
        return redirect('feed')

    # 만약 GET 요청이 들어올 경우, 문제 상세 페이지로 리디렉션
    return redirect('problem_detail', pk=pk)
