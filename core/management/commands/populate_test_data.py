import os
import requests
import random
import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models.board import Board, BoardCategory
from core.models.pet import Pet, Breed, AnimalType
from core.models.shop import Product, Category
from core.models.shorts import Shorts

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with realistic test data including embeddings for Breeds'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data population...')
        
        gms_key = os.environ.get('GMS_KEY')
        if not gms_key:
            self.stdout.write(self.style.WARNING('GMS_KEY not found. Using random embeddings.'))

        # 1. Users
        user = self.create_users()

        # 2. Board
        self.create_realistic_boards(user, gms_key)

        # 3. Breeds & Pets (New Logic)
        self.create_realistic_breeds_and_pets(user, gms_key)

        # 4. Products
        self.create_realistic_products(gms_key)

        # 5. Shorts
        self.create_realistic_shorts(user, gms_key)

        self.stdout.write(self.style.SUCCESS('Data population completed!'))

    def get_embedding(self, text, api_key):
        if not api_key:
            import numpy as np
            random_vector = np.random.rand(1536)
            norm = np.linalg.norm(random_vector)
            return (random_vector / norm).tolist()

        try:
            url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": "text-embedding-3-small",
                "input": text
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 429:
                time.sleep(1)
                return self.get_embedding(text, api_key)
            response.raise_for_status()
            return response.json()['data'][0]['embedding']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Embedding failed: {e}"))
            return self.get_embedding(None, None)

    def create_users(self):
        user, created = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        if created:
            user.set_password('password123')
            user.save()
        return user

    def create_realistic_boards(self, user, api_key):
        self.stdout.write('Creating Boards...')
        cat, _ = BoardCategory.objects.get_or_create(name='자유게시판')
        
        posts = [
            ("강아지가 자꾸 발을 핥아요", "산책 다녀와서 발을 닦아줬는데도 계속 핥아서 발바닥이 빨개졌어요. 습진일까요? 병원 가기 전에 연고 발라줘도 될까요? 경험 있으신 분 조언 부탁드립니다."),
            ("고양이 중성화 수술 후 관리 질문", "어제 6개월 된 수컷 고양이 중성화 수술을 했습니다. 넥카라를 너무 불편해해서 밥도 잘 안 먹는데 환묘복으로 갈아입혀도 될까요?"),
            ("강아지 분리불안 훈련 성공 후기", "출근만 하면 하울링하고 문 긁던 아이였는데, 켄넬 훈련이랑 5초, 10초 나갔다 오기 반복하면서 많이 좋아졌어요. 꾸준함이 답인 것 같습니다."),
            ("로얄캐닌 vs 힐스 사료 고민입니다", "1살 된 푸들 키우는데 입이 짧아서 사료를 잘 안 먹어요. 기호성 좋으면서도 건강에 좋은 사료 뭐가 좋을까요?"),
            ("고양이 양치질 어떻게 시키시나요?", "칫솔만 보면 도망가고 하악질해서 매일 전쟁입니다. 바르는 치약이라도 써야 할까요?"),
            ("슬개골 탈구 2기 진단 받았습니다", "산책하다가 다리를 절어서 병원 갔더니 슬개골 2기래요. 관절 영양제랑 미끄럼 방지 매트 말고 더 해줄 수 있는 게 있을까요?"),
            ("강아지랑 제주도 여행 가보신 분?", "비행기 탑승할 때 켄넬 사이즈 규정이 빡빡한가요? 5kg 말티즈인데 기내 반입 가능한 켄넬 추천 좀 해주세요."),
            ("고양이 화장실 모래 유목민입니다", "벤토나이트 쓰는데 먼지가 너무 날려서 눈곱이 자주 껴요. 먼지 적고 응고력 좋은 모래 추천 부탁드립니다."),
            ("강아지 배변패드 밖 싸는 버릇", "자꾸 패드 모서리에 싸서 바닥에 다 새요. 화장실 크기를 키워줘도 똑같은데 어떻게 교육해야 할까요?"),
            ("유기견 입양 고민 중입니다", "보호소 봉사 갔다가 눈에 밟히는 아이가 있는데, 직장인이라 혼자 있는 시간이 길어서 걱정이에요.")
        ]

        for title, content in posts: # Already 10 items
            if Board.objects.filter(title=title).exists():
                continue
            embedding = self.get_embedding(f"{title} {content}", api_key)
            Board.objects.create(title=title, content=content, category=cat, author=user, embedding=embedding)
            self.stdout.write(f"  Board created: {title}")

    def create_realistic_breeds_and_pets(self, user, api_key):
        self.stdout.write('Creating Breeds with RAG Knowledge...')
        dog_type, _ = AnimalType.objects.get_or_create(name='개')
        cat_type, _ = AnimalType.objects.get_or_create(name='고양이')

        # Import locally to avoid import error if model isn't migrated yet
        from core.models.pet import BreedKnowledge

        # Breeds RAG Data
        breeds_rag = [
            # 말티즈
            ("말티즈", dog_type, "성격 및 특징", "말티즈는 '참지 않지'라는 별명이 있을 정도로 자기주장이 강하지만, 기본적으로 사람을 매우 좋아하고 애교가 많습니다. 호기심이 왕성합니다."),
            ("말티즈", dog_type, "양육 주의사항", "눈물 자국 관리가 필수입니다. 또한 슬개골 탈구가 자주 발생하므로 미끄럼 방지 매트가 필요합니다."),
            ("말티즈", dog_type, "털 빠짐", "싱글 코트로 털 빠짐이 매우 적어 털 알러지가 있는 사람에게 적합합니다. 하지만 엉키지 않게 빗질은 자주 해줘야 합니다."),
            
            # 푸들
            ("푸들", dog_type, "지능", "보더콜리 다음으로 똑똑한 견종 2위입니다. 학습 능력이 뛰어나 배변 훈련이나 개인기 습득이 매우 빠릅니다."),
            ("푸들", dog_type, "털 관리", "곱슬거리는 털 덕분에 털이 거의 날리지 않습니다. 다만 귓속 털을 정리해주지 않으면 귓병이 생길 수 있습니다."),
            ("푸들", dog_type, "분리불안", "사람에 대한 의존도가 높아 혼자 두면 분리불안이 생길 확률이 높습니다. 어릴 때부터 독립심 훈련이 중요합니다."),

            # 비숑
            ("비숑 프리제", dog_type, "성격", "명랑하고 활발하며 '비숑 타임'이라 불리는 우다다 시간이 있습니다. 친화력이 좋아 다른 개들과도 잘 지냅니다."),
            ("비숑 프리제", dog_type, "미용", "특유의 하이바 컷을 유지하려면 미용비가 많이 듭니다. 털 관리가 까다로운 편입니다."),

            # 골든 리트리버
            ("골든 리트리버", dog_type, "특징", "천사견이라 불릴 정도로 인내심이 강하고 공격성이 없습니다. 아이가 있는 집에서도 키우기 좋습니다."),
            ("골든 리트리버", dog_type, "단점", "털이 상상 이상으로 많이 빠집니다. 실내에서 키운다면 로봇청소기는 필수입니다."),

            # 시바견
            ("시바견", dog_type, "엄살", "엄살이 심해 발톱만 깎으려 해도 비명을 지릅니다. '시바 스크림'이라고도 합니다."),
            ("시바견", dog_type, "고집", "자기 주관이 뚜렷해 산책 시 가기 싫으면 절대 움직이지 않는 '안 가 시바'를 시전합니다."),

            # 고양이들...
            ("코리안 숏헤어", cat_type, "특징", "유전적 다양성이 커서 튼튼하고 잔병치레가 적습니다. 개체마다 성격 차이가 크지만 대체로 적응력이 좋습니다."),
            ("러시안 블루", cat_type, "성격", "낯가림이 심해 낯선 사람에게는 숨지만, 주인에게는 '개냥이'처럼 애교를 부립니다."),
            ("먼치킨", cat_type, "건강", "다리가 짧아 척추 질환(디스크)에 취약합니다. 높은 곳에서 뛰어내리지 못하게 주의해야 합니다."),
            ("벵갈", cat_type, "활동량", "야생의 피가 섞여 활동량이 어마어마합니다. 캣휠 등 에너지를 소비할 수 있는 환경이 필요합니다."),
            ("스핑크스", cat_type, "피부 관리", "털이 없어 추위를 많이 타고, 피부에 기름이 끼기 때문에 주기적으로 목욕이나 닦아주기를 해야 합니다.")
        ]

        # Create Breeds first (without embedding initially, or simple one)
        breed_objs = {}
        for b_name, b_type, _, _ in breeds_rag:
            breed, _ = Breed.objects.get_or_create(name=b_name, animal_type=b_type)
            breed_objs[b_name] = breed

        # Create Knowledge
        for b_name, _, title, content in breeds_rag:
            full_text = f"{b_name} {title}: {content}"
            embedding = self.get_embedding(full_text, api_key)
            
            BreedKnowledge.objects.create(
                breed=breed_objs[b_name],
                title=title,
                content=content,
                embedding=embedding
            )
            self.stdout.write(f"  Knowledge created: {b_name} - {title}")

        # Pets linked to breeds (Simple instances)
        pets_list = ["구름이", "초코", "두부", "루비", "인절미"]
        breed_names = list(breed_objs.keys())
        
        for i, p_name in enumerate(pets_list):
            b_name = breed_names[i % len(breed_names)]
            Pet.objects.create(name=p_name, breed=breed_objs[b_name])

    def create_realistic_products(self, api_key):
        self.stdout.write('Creating Products...')
        cats = ['사료', '간식', '장난감', '용품', '의류']
        cat_objs = {name: Category.objects.get_or_create(name=name)[0] for name in cats}

        products = [
            ("유기농 연어 알러지 케어 사료 2kg", 32000, "사료", "가수분해 연어 단백질을 사용하여 식이 알러지를 최소화했습니다. 눈물 자국 개선에 효과적입니다."),
            ("국내산 오리안심 져키 300g", 15000, "간식", "100% 국내산 오리 안심을 저온 건조하여 영양소를 보존했습니다. 인공 첨가물이 없습니다."),
            ("삑삑이 라텍스 공 장난감 세트", 8900, "장난감", "천연 라텍스 소재로 만들어 치아에 무리가 가지 않습니다. 누르면 삑삑 소리가 납니다."),
            ("먼지 없는 벤토나이트 모래 6kg", 18000, "용품", "24번의 집진 공정을 거쳐 먼지를 99.9% 제거했습니다. 응고력과 탈취력이 뛰어납니다."),
            ("강아지 우비 올인원 레인코트", 28000, "의류", "비 오는 날 산책 필수템 방수 코팅 원단입니다. 밤 산책을 위한 반사 테이프가 있습니다."),
            ("대형견용 튼튼한 터그놀이 밧줄", 12000, "장난감", "촘촘하게 꼬아 만든 튼튼한 면 로프입니다. 대형견과 놀아주기 좋습니다."),
            ("고양이 낚싯대 리필용 깃털", 9900, "장난감", "다양한 모양의 깃털 리필입니다. 고양이의 사냥 본능을 자극합니다."),
            ("반려동물용 이발기 바리깡", 42000, "용품", "저소음 설계로 집에서 셀프 미용하기 좋습니다. 절삭력이 뛰어납니다."),
            ("강아지 겨울 패딩 점퍼", 36000, "의류", "안감이 후리스라 따뜻한 패딩입니다. 스냅 단추로 입히기 편합니다."),
            ("츄르 참치맛 대용량", 11000, "간식", "고양이가 좋아하는 참치맛 츄르입니다. 수분 보충에 좋습니다.")
        ]

        for title, price, cat_name, desc in products:
            if Product.objects.filter(title=title).exists():
                continue
            embedding = self.get_embedding(f"{title} {desc}", api_key)
            Product.objects.create(title=title, description=desc, base_price=price, category=cat_objs[cat_name], embedding=embedding)
            self.stdout.write(f"  Product created: {title}")

    def create_realistic_shorts(self, user, api_key):
        self.stdout.write('Creating Shorts...')
        
        shorts_data = [
            ("고양이 점프 실패 레전드영상 ㅋㅋ", "냉장고 위로 점프하다가 미끄러지는 고양이 ㅋㅋㅋ 다행히 안 다쳤어요."),
            ("강아지 자는 소리 들어보세요 (ASMR)", "드르렁 푸르르... 코 고는 소리가 사람 같아요. 힐링영상입니다."),
            ("간식 줬더니 '아이 러브 유'라고 말하는 강아지?", "옹알이하는 댕댕이 ㅋㅋㅋ 진짜 들어보면 아이 러브 유처럼 들려요!"),
            ("집사 몰래 간식 훔쳐 먹다 걸린 고양이", "서랍 여는 법을 터득했네요... 딱 걸리니까 모른 척 그루밍하는 거 봐요."),
            ("산책 거부하고 드러눕는 시바견", "안 가! 절대 안 가! 목줄 당겨도 꿈쩍도 안 하는 고집불통 시바..."),
            ("첫 목욕하는 아기 강아지의 반응", "물에 젖으니까 솜사탕이 사라졌어요 ㅠㅠ 낑낑대지도 않고 잘 씻네요."),
            ("고양이에게 오이를 보여줬더니...?", "화들짝 놀라서 점프하는 고양이 ㅋㅋ 오이가 뱀처럼 보여서 그렇대요."),
            ("주인 기다리는 강아지의 타임랩스", "출근하고 10시간 동안 현관문만 바라보고 있네요... 감동주의"),
            ("캣휠 타는 뱅갈 고양이 속도 실화냐", "무슨 치타인 줄 알았습니다. 쳇바퀴 돌아가는 소리가 엄청나요."),
            ("강아지 지능 테스트 1단계: 수건 탈출", "얼굴에 수건 덮어줬는데 3초 만에 탈출하네요! 천재견인가요?")
        ]

        for i, (title, desc) in enumerate(shorts_data):
            if Shorts.objects.filter(title=title).exists():
                continue
            embedding = self.get_embedding(f"{title} {desc}", api_key)
            Shorts.objects.create(title=title, description=desc, video_url=f"http://example.com/s{i}.mp4", author=user, embedding=embedding)
            self.stdout.write(f"  Shorts created: {title}")
