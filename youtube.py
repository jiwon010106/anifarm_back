from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
import os
import time

# Set a prefix and tags for clarity
youtube_router = APIRouter(
    prefix="/youtube-videos",
    tags=["YouTube"]
)

# 서버 사이드 캐싱
cached_videos = None
last_cache_time = None
CACHE_DURATION = 60 * 60  # 1시간(초 단위)


@youtube_router.get("")
async def get_youtube_videos():
    global cached_videos, last_cache_time

    # 캐시가 유효한 경우 캐시된 데이터 반환
    if cached_videos and last_cache_time and time.time() - last_cache_time < CACHE_DURATION:
        return cached_videos

    try:
        youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))

        request = youtube.search().list(
            part='snippet',
            q='작물 재배법',  # 검색어
            maxResults=15,   # 페이지 당 15개 영상 요청
            type='video'
        )
        response = request.execute()

        # 결과 캐싱
        cached_videos = response['items']
        last_cache_time = time.time()

        return cached_videos
    except Exception as e:
        print('YouTube API error:', e)
        raise HTTPException(status_code=500, detail="Failed to fetch YouTube videos")
