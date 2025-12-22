docker 접속
docker compose exec db psql -U mydjango mydjangodb

SELECT count(*) FROM core_board;
-- 제목과 임베딩 데이터 앞부분만 확인 (잘 들어갔는지)
SELECT title, substring(embedding::text, 1, 50) as vector_preview FROM core_board LIMIT 5;


SELECT name, breed_id, substring(embedding::text, 1, 50) as vector_preview FROM pet LIMIT 5;

SELECT title, base_price, substring(embedding::text, 1, 50) as vector_preview FROM product LIMIT 5;

SELECT title, substring(embedding::text, 1, 50) as vector_preview FROM core_shorts LIMIT 5;

종료
\q

fixture
docker-compose exec web python manage.py loaddata product.json
docker-compose exec web python manage.py loaddata user

데이터 save
docker compose exec web python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 -o db_clean_backup.json

데이터 load
docker compose exec web python manage.py loaddata db_all_backup.json

### shell 접속
- docker compose exec web python manage.py shell

```python
from core.tasks import update_popular_boards_daily
update_popular_boards_daily()
exit()
```

### Redis 데이터 조회
`docker compose exec redis redis-cli`
13시 버킷 확인
`ZRANGE board:views:H2025121913 0 -1 WITHSCORES`
사용자 최근 본 글 확인
`LRANGE user:1:recent 0 -1`
최종 인기글 캐시 확인
`GET board:popular:cache`
TTL 남은 시간 확인
`TTL board:views:H2025121913`

### db 용량 조회
docker exec -it django_pg_db du -sh /var/lib/postgresql/data/


docker-compose exec web python manage.py shell
```
from core.models import User
User.objects.get(email='chlendyd7@naver.com').delete()
exit()
```