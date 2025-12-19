import redis
import json
from django.conf import settings
from datetime import datetime, timedelta

class RedisService:
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
            cls._conn = redis.from_url(url, decode_responses=True)
        return cls._conn

    @classmethod
    def get_hour_bucket_key(cls, dt=None):
        if dt is None:
            dt = datetime.now()
        return f"board:views:H{dt.strftime('%Y%m%d%H')}"

    @classmethod
    def record_view(cls, user_id, board_id):
        r = cls.get_connection()
        
        # 1. 시간대별 글로벌 조회수 (ZSET)
        bucket_key = cls.get_hour_bucket_key()
        r.zincrby(bucket_key, 1, str(board_id))
        # 버킷 만료 시간 설정 (48시간 후 자동 삭제로 리소스 관리)
        r.expire(bucket_key, 172800) 

        # 2. 사용자별 최근 본 게시글 (List)
        if user_id:
            key = f'user:{user_id}:recent'
            r.lrem(key, 0, str(board_id))
            r.lpush(key, str(board_id))
            r.ltrim(key, 0, 19)

    @classmethod
    def get_user_recent_board_ids(cls, user_id):
        r = cls.get_connection()
        key = f'user:{user_id}:recent'
        return r.lrange(key, 0, 19)

    @classmethod
    def get_popular_ids_sliding_window(cls, hours=24, limit=10):
        r = cls.get_connection()
        
        # 최근 N시간의 키 목록 생성
        now = datetime.now()
        keys = [cls.get_hour_bucket_key(now - timedelta(hours=i)) for i in range(hours)]
        
        # 존재하는 키만 필터링
        existing_keys = [k for k in keys if r.exists(k)]
        
        if not existing_keys:
            return []

        # 임시 키에 합산 저장
        temp_key = "board:views:sliding_window_temp"
        r.zunionstore(temp_key, existing_keys)
        
        # 상위 ID 추출
        top_ids = r.zrevrange(temp_key, 0, limit - 1)
        
        # 임시 키 삭제
        r.delete(temp_key)
        
        return top_ids

    @classmethod
    def get_bucket_views(cls, bucket_key):
        r = cls.get_connection()
        return {item[0]: int(item[1])
            # 0 ~ -1 은 모든 데이터를 가져와라는 뜻
            for item in r.zrange(bucket_key, 0, -1, withscores=True)
        }

    @classmethod
    def cache_popular_board_ids(cls, board_ids):
        r = cls.get_connection()
        r.set('board:popular:cache', json.dumps(board_ids))

    @classmethod
    def get_cached_popular_board_ids(cls):
        r = cls.get_connection()
        data = r.get('board:popular:cache')
        if data:
            return json.loads(data)
        return []
