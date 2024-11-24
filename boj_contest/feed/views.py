from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Feed 
from competition.models import Submission,Participant,ContestProblem
from django.http import HttpResponseBadRequest
from django.db.models import Count, Q
@login_required
def feed_view(request):
    # 피드 항목을 생성일 내림차순으로 가져옵니다
    feed_items = Feed.objects.select_related('problem').order_by('-created_at')

    # 현재 로그인한 사용자의 Participant 인스턴스를 가져옵니다
    try:
        participant = get_object_or_404(Participant, user_id=request.user)
    except Participant.DoesNotExist:
        participant = None

    if participant:
        # 사용자가 맞춘 문제의 ID 집합
        solved_problem_ids = set(
            Submission.objects.filter(user_id=participant, is_correct=True)
                                .values_list('problem_id', flat=True)
        )
    else:
        solved_problem_ids = set()

    # 피드에 포함된 모든 문제의 ID 리스트
    problem_ids = [item.problem.id for item in feed_items]

    # 각 문제별로 맞춘 사용자 수를 계산 (is_correct=True인 경우만)
    solved_counts = Submission.objects.filter(problem_id__in=problem_ids, is_correct=True) \
                                      .values('problem_id') \
                                      .annotate(solved_count=Count('user_id', distinct=True))

    # 문제 ID를 키로 하고 solved_count를 값으로 하는 딕셔너리 생성
    solved_counts_dict = {item['problem_id']: item['solved_count'] for item in solved_counts}

    # 피드 항목에 is_solved와 solved_count 추가
    for item in feed_items:
        item.is_solved = item.problem.id in solved_problem_ids
        item.solved_count = solved_counts_dict.get(item.problem.id, 0)

    return render(request, 'feed/feed.html', {'feed_items': feed_items})

@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(ContestProblem, problem_id=problem_id)
    
    # is_correct=True인 제출을 한 고유한 사용자 수를 카운트
    solved_count = Submission.objects.filter(problem_id=problem, is_correct=True) \
                                     .values('user_id') \
                                     .distinct() \
                                     .count()
    
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
