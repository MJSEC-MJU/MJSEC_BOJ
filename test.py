import requests
import sqlite3

# 데이터베이스 연결 설정
conn = sqlite3.connect('solved_problems.db')
cursor = conn.cursor()

# 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS solved_problems (
    user_id TEXT,
    problem_id INTEGER,
    PRIMARY KEY (user_id, problem_id)
)
''')
conn.commit()

def fetch_all_solved_problems(user_id):
    base_url = "https://solved.ac/api/v3/search/problem"
    page = 1
    
    while True:
        params = {
            "query": f"solved_by:{user_id}",
            "page": page
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # HTTP 오류 발생 시 예외처리
        except requests.RequestException as e:
            print(f"Failed to fetch data: {e}")
            break
        
        data = response.json()
        problems = data.get('items', [])
        
        if not problems:
            break
        
        try:
            with conn:
                for problem in problems:
                    cursor.execute('''
                    INSERT OR IGNORE INTO solved_problems (user_id, problem_id) VALUES (?, ?)
                    ''', (user_id, problem['problemId']))
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        
        if len(problems) < 50:
            break
        
        page += 1

def update_newly_solved_problems(user_id, problem_id):
    base_url = "https://solved.ac/api/v3/search/problem"
    
    # 사용자가 문제를 이미 풀었는지 확인
    if is_problem_solved_by_user(user_id, problem_id):
        return

    # 전체 푼 문제 수를 가져오기 위한 요청
    summary_url = f"https://solved.ac/api/v3/user/show?handle={user_id}"
    try:
        response = requests.get(summary_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return
    
    data = response.json()
    total_problems_solved = data.get('solvedCount', 0)
    
    # 최대 페이지 수 계산
    page_size = 50
    max_page = (total_problems_solved + page_size - 1) // page_size
    
    # 이중 탐색을 통해 문제 ID가 포함된 페이지 찾기
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
        except requests.RequestException as e:
            print(f"Failed to fetch data: {e}")
            return
        
        data = response.json()
        problems = data.get('items', [])
        
        if not problems:
            high = mid - 1
            continue
        
        min_problem_id = problems[0]['problemId']
        max_problem_id = problems[-1]['problemId']
        
        if min_problem_id <= problem_id <= max_problem_id:
            new_problems = [p for p in problems if not is_problem_solved_by_user(user_id, p['problemId'])]
            if new_problems:
                try:
                    with conn:
                        for problem in new_problems:
                            cursor.execute('''
                            INSERT OR IGNORE INTO solved_problems (user_id, problem_id) VALUES (?, ?)
                            ''', (user_id, problem['problemId']))
                except sqlite3.Error as e:
                    print(f"Database error: {e}")
            break
        elif problem_id < min_problem_id:
            high = mid - 1
        else:
            low = mid + 1

def is_problem_solved_by_user(user_id, problem_id):
    cursor.execute('''
    SELECT 1 FROM solved_problems WHERE user_id = ? AND problem_id = ?
    ''', (user_id, problem_id))
    return cursor.fetchone() is not None

# 초기 문제 해결 정보 업데이트
user_id = "ialleejy"
# fetch_all_solved_problems(user_id)

# 특정 문제가 해결되었는지 확인
problem_id = 4470

# 사용자가 해당 문제를 풀었는지 확인하고, 주기적으로 새로운 문제 해결 정보 업데이트
if is_problem_solved_by_user(user_id, problem_id):
    print(f"User {user_id} has solved problem {problem_id}.")
else:
    update_newly_solved_problems(user_id, problem_id)
    if is_problem_solved_by_user(user_id, problem_id):
        print(f"User {user_id} has solved problem {problem_id}.")
    else:
        print(f"User {user_id} has not solved problem {problem_id}.")

# 데이터베이스 연결 닫기
conn.close()
