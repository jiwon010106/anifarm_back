import requests # 웹 스크래핑 과정에서 http 요청을 통해 데이터를 가져오기 위한 라리브러리
import asyncio    # 동기 함수를 비동기로 감싸기 위해 사용
from bs4 import BeautifulSoup # 뷰티풀 수프 라이브러리
from urllib.parse import urljoin
import aiohttp

html = """
  <html>
    <body>
      <h1 id='title'>파이썬 스크래핑</h1>
      <p id='body'>웹 데이터 수집</p>
      <p class='scraping'>삼성전자 일별 시세 불러오기</p>
      <p class='scraping'>4만 전자에서 7만 전자로...</p>
    </body>
  </html>
"""

soup = BeautifulSoup(html, 'html.parser')


stock_url = 'https://www.nongmin.com/economyMain'
res = requests.get(stock_url)
html = res.text # 응답에서 html 문서만 가져오기

# print(html)

# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
# text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7

# 헤더값 설정
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
               'image/avif,image/webp,image/apng,*/*;q=0.8,'
               'application/signed-exchange;v=b3;q=0.7')
}

# 헤더를 담아서 요청
res = requests.get(stock_url, headers=headers)
html = res.text

# res.text 를 뷰티풀수프에 전달하여 html.parser로 파싱
soup = BeautifulSoup(html, 'html.parser')
print(soup.find_all('tr'))

# 동기 뉴스 링크 스크레이핑 함수
def scrape_news_links(url: str = 'https://www.nongmin.com/list/19', pages: int = 1):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    aggregated_links = []
    
    # 지정된 페이지 수만큼 반복 (페이지네이션 처리)
    for page in range(1, pages + 1):
        # 첫 페이지는 기본 url 사용, 그 외에는 ?page=번호 를 추가합니다.
        if page == 1:
            page_url = url
        else:
            page_url = f"{url}?page={page}"
            
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 뉴스 영역 찾기
        news_section = soup.find('div', class_='news_list news_content')
        if not news_section:
            continue
        
        # 기사 리스트는 LEFT_NEWS_LIST 영역 아래에 있는 <ul class="common_list">
        left_news_list_container = news_section.find('div', attrs={'data-layout-area': 'LEFT_NEWS_LIST'})
        if not left_news_list_container:
            continue
        
        common_list = left_news_list_container.find('ul', class_='common_list')
        if not common_list:
            continue

        # 각 <li> 항목 내의 <a> 태그에서 기사 링크 및 제목 추출
        for li in common_list.find_all('li'):
            a_tag = li.find('a', href=True)
            if not a_tag:
                continue

            link_href = a_tag['href']
            # '/article/'로 시작하는 경우에만 처리합니다.
            if not link_href.startswith('/article/'):
                continue

            title_pre = a_tag.find('pre', class_='tit')
            title = title_pre.get_text(strip=True) if title_pre else a_tag.get_text(strip=True)

            full_link = urljoin(url, link_href)
            aggregated_links.append({
                'title': title,
                'link': full_link
            })
        
    return aggregated_links

# 동기 함수(scrape_news_links)를 비동기로 감싸는 함수
async def async_scrape_news_links(url: str = 'https://www.nongmin.com/list/19', pages: int = 1):
    return await asyncio.to_thread(scrape_news_links, url, pages)

# 비동기 HTTP 요청 함수
async def async_fetch(url: str, headers: dict):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

# 뉴스 기사에서 이미지 URL 추출
async def async_scrape_news_image(article_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    html_content = await async_fetch(article_url, headers)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. <div class="article-image"> 내부의 <img> 태그 검사
    image_container = soup.find('div', class_='article-image')
    if image_container:
        img_tag = image_container.find('img')
        if img_tag:
            img_src = img_tag.get('src')
            if img_src:
                return urljoin(article_url, img_src)
    
    # 2. Open Graph 메타 태그 검사
    og_image_tag = soup.find("meta", property="og:image")
    if og_image_tag:
        og_image = og_image_tag.get("content")
        if og_image:
            return urljoin(article_url, og_image)
    
    # 이미지 URL을 찾지 못한 경우
    return None

# 뉴스 기사에서 내용 추출
async def async_scrape_news_content(article_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    html_content = await async_fetch(article_url, headers)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. news_content_box 내부의 컨텐츠 추출
    content_box = soup.find('div', class_='news_content_box')
    if content_box:
        news_container = content_box.select_one("div.news_txt.ck-content")
        if news_container:
            # <p> 태그 내부의 텍스트를 우선 추출합니다.
            paragraphs = news_container.find_all("p")
            if paragraphs:
                content = "\n".join(p.get_text(strip=True) for p in paragraphs)
                if content:
                    return content
            # 만약 <p> 태그로는 내용이 추출되지 않으면, 전체 텍스트를 확인합니다.
            content = news_container.get_text(separator="\n", strip=True)
            # 텍스트가 없으면 QR코드 관련 내용으로 판단하여 메시지를 반환합니다.
            if not content:
                return "QR코드를 찍어보세요!"
            return content
    
    # 2. 별도 뉴스 컨테이너 처리
    news_container = soup.select_one("div.news_txt.ck-content")
    if news_container:
        # 전체 텍스트 추출 또는 <p> 태그만 선택할 수 있습니다.
        paragraphs = news_container.find_all("p")
        if paragraphs:
            content = "\n".join(p.get_text(strip=True) for p in paragraphs)
            if content:
                return content
        # 만약 <p> 태그가 없다면, 컨테이너 전체의 텍스트를 사용합니다.
        content = news_container.get_text(separator="\n", strip=True)
        if content:
            return content
    
    # 3. 대체 방식: article-content 처리
    content_container = soup.find('div', class_='article-content')
    if content_container:
        text = content_container.get_text(separator="\n", strip=True)
        if text:
            return text
    
    # 4. 마지막 fallback: inline 스타일의 p 태그
    paragraphs = soup.select('p[style]')
    if paragraphs:
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)
        if content:
            return content
    
    return None

if __name__ == '__main__':
    # 테스트: 동기 함수 호출 예제
    links = scrape_news_links()
    for news in links:
        print(f"Title: {news['title']}, Link: {news['link']}")
