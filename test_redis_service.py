# docker compose exec web python test_redis_service.py
import os
import django
import sys
import json
from datetime import datetime, timedelta

# Django 환경 설정 (프로젝트 내부 서비스 임포트를 위함)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.services.redis import RedisService

def test_redis_logic():
    print("\n" + "="*50)
    print("🚀 RedisService 데이터 구조 및 리턴값 테스트")
    print("="*50)

    r = RedisService.get_connection()
    test_user_id = 9999
    
    # --- 초기화 (기존 테스트 데이터 삭제) ---
    r.delete(f'user:{test_user_id}:recent')
    r.delete('board:popular:cache')

    # 오늘 생성된 버킷들 정리 (테스트 편의상)
    now = datetime.now()
    for i in range(24):
        r.delete(RedisService.get_hour_bucket_key(now - timedelta(hours=i)))

    # --- 1. record_view 테스트 ---
    print("\n[1] record_view: 조회수 및 유저 이력 기록")
    print("Action: User 9999가 게시글 1, 2, 3을 순서대로 조회")
    RedisService.record_view(test_user_id, 1)
    RedisService.record_view(test_user_id, 2)
    RedisService.record_view(test_user_id, 3)
    # 비로그인 사용자 환경
    RedisService.record_view(None, 1) 
    RedisService.record_view(None, 1)

    # --- 2. 최근 본 게시글 조회 ---
    print("\n[2] get_user_recent_board_ids (List 구조)")
    recent_ids = RedisService.get_user_recent_board_ids(test_user_id)
    print(f"👉 Return (최신순): {recent_ids}")
    print(f"💡 설명: r.lrange를 통해 가져온 리스트입니다. (최신 데이터가 앞쪽)")



    # --- 4. 슬라이딩 윈도우 (합산) 테스트 ---
    print("\n[4] get_popular_ids_sliding_window (ZUNIONSTORE 사용)")
    # 과거 데이터 목업 생성
    past_key = RedisService.get_hour_bucket_key(now - timedelta(hours=2))
    r.zincrby(past_key, 10, "100") # 2시간 전에 게시글 100번이 10번 조회됨
    print(f"Action: 2시간 전 버킷({past_key})에 게시글 100번(조회수 10) 추가")

    popular_ids = RedisService.get_popular_ids_sliding_window(hours=24, limit=5)
    print(f"👉 Return (합산된 상위 ID): {popular_ids}")
    print(f"💡 설명: 현재 버킷과 과거 버킷을 합쳐서 가장 조회수가 높은 글들이 나옵니다.")

    # --- 5. 최종 결과 캐싱 ---
    print("\n[5] cache_popular_board_ids & get_cached_popular_board_ids (String 구조)")
    mock_result = ["100", "1", "2"]
    RedisService.cache_popular_board_ids(mock_result)
    print(f"Action: 최종 순위 {mock_result}를 캐시에 저장")
    
    cached_data = RedisService.get_cached_popular_board_ids()
    print(f"👉 Return (JSON Load 결과): {cached_data}")
    print(f"💡 설명: Celery가 계산한 최종 결과를 API가 빠르게 읽기 위해 단순 String(JSON)으로 저장한 값입니다.")

    print("\n" + "="*50)
    print("✅ 테스트 완료")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_redis_logic()
