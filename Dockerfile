# 파이썬 베이스 이미지
FROM python:3.11-slim

# 필요한 환경 변수 설정
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV development

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 종속성 설치 (DB 대기 스크립트를 위한 netcat 설치)
RUN apt-get update \
    && apt-get install -y netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 종속성 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . /app/

# 엔트리포인트 스크립트 설정
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
