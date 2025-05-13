import asyncio
import datetime
import time
import re
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from instagrapi.exceptions import FeedbackRequired
from api.insta import Insta
from api.model.payload import InstagramLogin, LimitByWeeks

app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

insta = Insta()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_users = ["doto.ri_","gangggi_e_you","kang_mayo","sso._.hani_","terry_k_0225","pinkmongkii","hyejin_7931","okhee0717","yehyun_oo","haemi.fit","reumssi","_misogood","wldbsdk3","mina.c","youngjoo_peach","ssum_nam","jieunisong","sssungho_hoya","doong_onni"]
limit_by_weeks = 3
reject_messages = ["님을 내보냈습니다.", "님이 들어왔습니다.", "님이 나갔습니다.", "운영정책을 위반한 메시지로 신고 접수 시 카카오톡 이용에 제한이 있을 수 있습니다.", "불법촬영물", "유의하여 주시기 바랍니다.", "님과 카카오톡 대화", "저장한 날짜 : ", "ex )", "[공지]"]

@app.post("/api/py/files")
async def upload_file(file: UploadFile = File(...)):
    print("품앗이 브레이커들 잡으러 가는 중...")
    content = await file.read()
    text = content.decode('utf-8')

    message_pattern = re.compile(
        fr"\[(.*?)\] \[오. (.*?)\]\s*(.*?)\s*(https://www\.instagram\.com[^\s]+)\s*((?:.|\n)*?/{limit_by_weeks})",
        re.MULTILINE
    )

    # 품앗이 대상 피드/릴스 캐치
    print("품앗이 대상 피드 캐치 중...")
    messages = message_pattern.findall(text)
    print(f"품앗이 대상 피드 건수: {len(messages)}개")
    date_pattern = re.compile(r"^--------------- (\d{4}년 \d{1,2}월 \d{1,2}일 [^ ]+) ---------------$")
    current_date = None
    
    result = {}

    for line in text.splitlines():
        # 불필요 메시지 건너뛰기
        if any(reject in line for reject in reject_messages):
            print("건너뛰기...")
            continue

        # 카톡 내용 날짜 캐치
        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            print("날짜 캐치!")
            continue
        
        # 품앗이 대상 피드/릴스가 있는 메시지면 해당 날짜에 대해서 카톡 닉네임과 인스타 링크 맵핑
        # 날짜를 알아야하기 때문에 모든 라인에 대해서 실행함
        print("품앗이 대상 피드 날짜별로 맵핑 중...")
        if current_date:
            for match in messages:
                if match[3] in line:
                    if current_date not in result:
                        result[current_date] = []
                    result[current_date].append({
                        "username": str(match[0]).split("@")[1],
                        "link": match[3].strip()
                    })
                    messages.remove(match)
                    break

    username_counts = defaultdict(int)
    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)

    # 일주일 이전 품앗이 요청건에 대해서 개인별 카운팅
    print("개인별 품앗이 요청건 카운트 중...")
    for date_str, entries in result.items():
        year, month, day = map(int, re.findall(r'\d+', date_str))
        date = datetime.datetime(year, month, day)

        if date >= one_week_ago:
            week_start = date - datetime.timedelta(days=date.weekday())
            week_end = week_start + datetime.timedelta(days=6)
            
            for entry in entries:
                week_range = f"{week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}"
                username_counts[(entry["username"], week_range)] += 1

    final_counts = {f"{username}": f"{count}/{limit_by_weeks}" for (username, week_range), count in username_counts.items()}

    catcha_rule_breakers = {}
    for k, v in final_counts.items():
        catcha_rule_breakers[k] = v

    # 품앗이 안한 인원 선별
    print("품앗이 안한 인원 선별 중...(오래걸림)")
    async def get_user_actions(entry):
        # 좋아요는 인스타그램 정책상 랜덤으로 최대 100여건만 받을 수 있어서 체크 못함
        # 인스타그램 정책상 too many request가 발생확률이 높아도 동기로 하나씩 천천히 가져와야 함

        comment_by = []

        while not comment_by:
            comment_by = insta.get_comment_until_success(entry['link'])
            print(f"{entry['link']}: {comment_by}")

        # if comment_by is None:
        #     return [], entry['link']

        outsiders = [
            user for user in current_users if user not in comment_by
        ]
        outsiders = [user for user in outsiders if user != entry['username']]

        return outsiders, entry['link']

    catcha_outsiders = {}
    for entries in result.values():
        for entry in entries:
            actions = await get_user_actions(entry)
            print(actions)
            outsiders, link = actions
            if outsiders:
                catcha_outsiders[link] = outsiders

    return {"rule_breakers": catcha_rule_breakers, "outsiders": catcha_outsiders}

@app.post("/api/py/login/instagram")
async def login_instagram(body: InstagramLogin):
    insta.login(body.verification_code)

@app.post("/api/py/users")
async def update_users(users: list[str]):
    global current_users
    current_users = users
    return {"users": current_users}

@app.post("/api/py/limit_by_weeks")
async def update_limit_by_weeks(body: LimitByWeeks):
    global limit_by_weeks
    limit_by_weeks = body.limit
    return {"limit_by_weeks": limit_by_weeks}

@app.get("/api/py/role")
def get_roles():
    return {"users": current_users, "limit_by_weeks": limit_by_weeks}