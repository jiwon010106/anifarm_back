import asyncio
from fastapi import APIRouter, HTTPException, Query
from . import crawler  # 상대 import 사용

router = APIRouter()

@router.get("/news-links", tags=["Crawler"])
async def get_news_links(               
    list_id: int = Query(19, alias="list"),
    pages: int = Query(2, description="스크랩할 페이지 수 (기본값 2)")
):
    """
    뉴스 관련 링크를 크롤링하여 반환합니다.
    각 뉴스 기사에 대해 이미지 URL과 내용도 함께 추가합니다.
    Query parameter 'list'를 통해 크롤링할 URL 번호를 지정하며,
    'pages' 파라미터로 추가 페이지 수를 지정할 수 있습니다.
      - /news-links?list=19 : 첫 페이지 (SaleNews 기본값)
      - /news-links?list=19&pages=2 : 1~2 페이지의 뉴스 기사 스크랩
    """
    try:
        # list_id를 통해 크롤링 대상 URL 생성
        url = f"https://www.nongmin.com/list/{list_id}"
        # 뉴스 링크 추출 함수도 비동기로 작성하는 것이 좋습니다.
        news_links = await crawler.async_scrape_news_links(url, pages)
        tasks = []
        
        # 각 뉴스 링크에 대해 이미지와 내용을 병렬로 가져오기 위한 작업 생성
        for item in news_links:
            tasks.append(_fetch_additional_info(item))
        await asyncio.gather(*tasks)
        return {"news_links": news_links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _fetch_additional_info(item):
    # 이미지와 내용을 동시에 비동기 요청
    image_url, content = await asyncio.gather(
         crawler.async_scrape_news_image(item["link"]),
         crawler.async_scrape_news_content(item["link"])
    )
    item["image"] = image_url
    item["content"] = content
    
    