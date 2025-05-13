import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import datetime
from warnings import catch_warnings
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import re
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
catcha_outsiders = ""

@app.post("/api/py/files")
async def upload_file(file: UploadFile = File(...)):
    global catcha_outsiders
    content = await file.read()
    text = content.decode('utf-8')

    message_pattern = re.compile(
        fr"\[(.*?)\] \[오. (.*?)\]\s*(.*?)\s*(https://www\.instagram\.com[^\s]+)\s*((?:.|\n)*?/{limit_by_weeks})",
        re.MULTILINE
    )

    messages = message_pattern.findall(text)
    date_pattern = re.compile(r"^--------------- (\d{4}년 \d{1,2}월 \d{1,2}일 [^ ]+) ---------------$")
    current_date = None
    
    result = {}

    for line in text.splitlines():
        if any(reject in line for reject in reject_messages):
            continue

        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            continue
        
        if current_date:
            for match in messages:
                if match[3] in line:
                    if current_date not in result:
                        result[current_date] = []
                    result[current_date].append({
                        "username": match[0],
                        "link": match[3].strip()
                    })
                    messages.remove(match)
                    break

    username_counts = defaultdict(int)
    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)

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

    notification_message = await generate_notification_message(final_counts)
    catcha_outsiders += notification_message

    async def get_user_actions(entry, executor):
        loop = asyncio.get_event_loop()
        comment_by = await loop.run_in_executor(executor, insta.get_comment_by, entry['link'])

        if comment_by is None:
            return [], entry['link']

        doesnt_do = [
            user for user in current_users if user not in comment_by
        ]
        doesnt_do = [user for user in doesnt_do if user != entry['username']]

        return doesnt_do, entry['link']

    pool = ThreadPoolExecutor()

    try:
        notification_message = ""
        tasks = [get_user_actions(entry, pool) for entries in result.values() for entry in entries]
        results = await asyncio.gather(*tasks)
        if results is not None:
            for doesnt_do, link in results:
                if doesnt_do:
                    notification_message += f"[{link}] 안한 사람:\n{doesnt_do}\n"
        
            catcha_outsiders += notification_message
    finally:
        pool.shutdown()

    return {"outsiders": catcha_outsiders}

async def generate_notification_message(final_counts):
    return '\n'.join([f"{k}: {v}" for k, v in final_counts.items()]) + "\n\n\n"

# @app.post("/api/py/files")
# async def upload_file(file: UploadFile = File(...)):
#     content = await file.read()
#     text = content.decode('utf-8')

#     message_pattern = re.compile(
#         fr"\[(.*?)\] \[오. (.*?)\]\s*(.*?)\s*(https://www\.instagram\.com[^\s]+)\s*((?:.|\n)*?/{limit_by_weeks})",
#         re.MULTILINE
#     )

#     messages = message_pattern.findall(text)

#     date_pattern = re.compile(r"^--------------- (\d{4}년 \d{1,2}월 \d{1,2}일 [^ ]+) ---------------$")
#     current_date = None
    
#     result = {}
    
#     for line in text.splitlines():
#         if any(reject in line for reject in reject_messages):
#             continue

#         date_match = date_pattern.match(line)
#         if date_match:
#             current_date = date_match.group(1)
#             continue
        
#         if current_date:
#             for match in messages:
#                 if match[3] in line:
#                     if current_date not in result:
#                         result[current_date] = []
#                     result[current_date].append({
#                         "username": match[0],
#                         "link": match[3].strip()
#                     })
#                     messages.remove(match)
#                     break

#     # for date, entries in result.items():
#     #     print(f"\n 날짜: {date}")
#     #     for i, entry in enumerate(entries, start=1):
#     #         print(f"\n  메시지 {i}")
#     #         print(f"    - 사용자명 (username): {entry['username']}")
#     #         print(f"    - 링크 (link): {entry['link']}")

#     username_counts = defaultdict(int)
#     today = datetime.datetime.now()
#     one_week_ago = today - datetime.timedelta(days=7)

#     for date_str, entries in result.items():
#         year, month, day = map(int, re.findall(r'\d+', date_str))
#         date = datetime.datetime(year, month, day)

#         if date >= one_week_ago:
#             week_start = date - datetime.timedelta(days=date.weekday())
#             week_end = week_start + datetime.timedelta(days=6)
            
#             for entry in entries:
#                 week_range = f"{week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}"
#                 username_counts[(entry["username"], week_range)] += 1


#     final_counts = {f"{username}": f"{count}/{limit_by_weeks}" for (username, week_range), count in username_counts.items()}

#     notification_message = ""
#     for k, v in final_counts.items():
#         notification_message += k
#         notification_message += ": "
#         notification_message += v
#         notification_message += "\n"
#     asyncio.create_task(notification.send_message(notification_message))

#     notification_message = ""
#     for date, entries in result.items():
#         for i, entry in enumerate(entries, start=1):
#             comment_by = insta.get_comment_by(entry['link'])
#             if comment_by is not None:
#                 like_by = insta.get_like_by(entry['link'])
#             if comment_by is not None and like_by is not None:
#                 doesnt_do = [user for user in current_users if user not in comment_by or user not in like_by]
#                 doesnt_do = [user for user in doesnt_do if user != entry['username']]

#                 if doesnt_do:
#                     notification_message += f"{doesnt_do}들이 안함: {entry['link']}"
#                     notification_message += "\n"
#     asyncio.create_task(notification.send_message(notification_message))

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