import os
import time
import traceback
from typing import List, Tuple
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.types import Comment, UserShort

load_dotenv()

class Insta():
    def __init__(self):
        self.client = Client()

    def login(self, verification_code: str):
        self.client.load_settings
        self.client.login(os.getenv('insta_username'), os.getenv('insta_password'), verification_code=verification_code)
        self.client.dump_settings("session.json")

    def get_comment_by(self, uri: str) -> list[str]:
        try:
            print(f"{uri} 댓글 가져오는 중...")
            time.sleep(5)
            self.client.load_settings("session.json")
            media_pk = self.client.media_pk_from_url(uri)
            media_id = self.client.media_id(media_pk)
            comments: Tuple[List[Comment], str] = self.client.media_comments_chunk(media_id=media_id, max_amount=10000)
            print(comments)
            return list({comment.user.username for comment in comments[0] if comment.user.username})
        except Exception as e:
            print(f"Failed search comments: {uri}")
        finally:
            self.client.dump_settings("session.json")
            
    def get_like_by(self, uri: str) -> list[str]:
        try:
            self.client.load_settings("session.json")
            media_pk = self.client.media_pk_from_url(uri)
            media_id = self.client.media_id(media_pk)
            likers:List[UserShort] = self.client.media_likers(media_id=media_id)
            self.client.dump_settings("session.json")
            return list({user.username for user in likers if user.username})
        except Exception as e:
            print(f"Failed search likers: {uri}")
            print(e)