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

### shell 접속
- docker compose exec web python manage.py shell

###
```python
from core.tasks import update_popular_boards_daily
update_popular_boards_daily()
exit()
```