# MJSEC_BOJ
### 프로젝트 소개
MJSEC 백준 프로그래밍 대회를 위한 웺사이트 입니다.

# MJSEC_CTF_CHALLENGE


### 주요 기능

- **다이나믹 스코어링 시스템**: 실시간으로 점수를 계산하여 참가자들에게 즉각적인 피드백 제공
- **AJAX 기반 리더보드**: fetch API를 활용하여 실시간으로 업데이트되는 리더보드 구현
- **문제 제출 및 검증 시스템**: python requests 모듈을 활용하여 solved ac api를 통한 검증시스템 구현
- **사용자 및 팀 관리**: 참가자를 관리자 페이지에서 효율적으로 관리할 수 있는 기능


| 항목              | 뱃지                                                                                                      |
|-------------------|-----------------------------------------------------------------------------------------------------------|
| **OS**            | ![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04_LTS-CC3534?logo=ubuntu&logoColor=white)              |
| **서버**          | ![Google Cloud](https://img.shields.io/badge/Google%20Cloud-GCP_E2_model-4285F4?logo=google-cloud)         |
| **웹 프레임워크** | ![Django](https://img.shields.io/badge/Django-5.1-green?logo=django)                                      |
| **데이터베이스**  | ![SQLite](https://img.shields.io/badge/SQLite-latest-B3B3B3?logo=sqlite)                                  |
| **배포 도구**     | ![Docker](https://img.shields.io/badge/Docker-latest-blue?logo=docker) <br> ![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2.21.0-blue?logo=docker) |
| **웹 서버**       | ![Gunicorn](https://img.shields.io/badge/Gunicorn-20.1.0-343434?logo=gunicorn) <br> ![Nginx](https://img.shields.io/badge/Nginx-latest-009639?logo=nginx) |
| **버전 관리**     | ![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white)               |




## 서버 설치 단계
1. 시스템 패키지 업데이트 및 Docker 설치:
    ```sh
    sudo apt update
    sudo apt install docker.io
    sudo systemctl enable --now docker
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    docker-compose --version
    ```

2. 프로젝트 클론:
    ```sh
    git clone https://github.com/MJSEC-MJU/MJSEC_BOJ.git
    cd MJSEC_BOJ/boj_contest
    ```

## 가상환경 설정
1. Python 가상환경 설치:
    ```sh
    sudo apt-get install python3-venv
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Secret Key 생성:
    ```sh
    python -c 'import secrets; print(secrets.token_urlsafe(50))'
    ```
    생성된 Secret Key를 `boj_contest/settings.py` 파일의 `SECRET_KEY` 변수에 추가합니다.

3. `boj_contest/settings.py` 파일에서 `ALLOWED_HOSTS` 설정 변경:
    ```python
    ALLOWED_HOSTS = ["your_domain"]
    ```

## 도커 컨테이너 실행
1. Docker Compose 빌드 및 실행:
    ```sh
    sudo docker-compose build
    sudo docker-compose up -d
    ```
이제 프로젝트가 Docker 컨테이너에서 실행됩니다.

## 도커 컨테이너에서 관리자 계정생성
1. Docker 컨테이너 진입 및 생성
   ```sh
    sudo docker-compose exec web /bin/sh
    python manage.py createsuperuser
    ```
