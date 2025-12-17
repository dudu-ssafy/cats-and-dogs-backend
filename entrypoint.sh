#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# DB 접속 정보 (docker-compose의 서비스 이름 'db' 사용)
HOST="db" 
PORT="5432"

# 1. 데이터베이스가 연결을 수신할 준비가 될 때까지 대기
echo "Waiting for PostgreSQL ($HOST:$PORT) to start..."
while ! nc -z $HOST $PORT; do
  sleep 0.5
done
echo "PostgreSQL started!"

# 2. Django 마이그레이션 실행
echo "Running migrations..."
python manage.py migrate

# 3. 메인 명령 실행 (docker-compose.yml의 command가 실행됨)
exec "$@"