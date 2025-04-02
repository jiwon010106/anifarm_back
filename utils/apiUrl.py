import os
from dotenv import load_dotenv
import aiohttp
import json
import urllib.parse

# 환경 변수 로딩
load_dotenv()

API_KEY = os.getenv('WEATHER_API_KEY')
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# 한국 주요 도시 매핑 (한글:영문)
KOREAN_CITIES = {
    "서울": "Seoul",
    "부산": "Busan",
    "인천": "Incheon",
    "대구": "Daegu",
    "대전": "Daejeon",
    "광주": "Gwangju",
    "울산": "Ulsan",
    "제주": "Jeju"
}

async def fetchWeatherData(city):
    try:
        # 한글 도시명을 영문으로 변환
        english_city = KOREAN_CITIES.get(city, city)
        
        async with aiohttp.ClientSession() as session:
            params = {
                'q': f"{english_city},KR",  # 국가 코드 추가
                'appid': API_KEY,
                'units': 'metric',
                'lang': 'kr'
            }
            
            async with session.get(BASE_URL, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise ValueError(f"날씨 API 오류: {error_data.get('message', '알 수 없는 오류')}")
                    
                raw_data = await response.json()
                processed_data = processWeatherData(raw_data)
                
                # 한글 도시명 추가
                processed_data['korean_name'] = city if city in KOREAN_CITIES else english_city
                return processed_data
                
    except Exception as e:
        print(f"날씨 데이터를 가져오는데 실패했습니다: {str(e)}")
        raise e

def processWeatherData(weatherData):
    try:
        list_data = weatherData.get('list', [])
        if not list_data:
            raise ValueError("날씨 데이터가 비어있습니다")

        # 현재, 내일, 주간 데이터 처리
        current_data = list_data[0]
        tomorrow_data = list_data[1]
        weekly_data = list_data[1:6]  # 5일치 데이터

        # 데이터 형식 변환
        processed = {
            'current': {
                'avg temp': current_data['main']['temp'],
                'max temp': current_data['main']['temp_max'],
                'min temp': current_data['main']['temp_min'],
                'rainFall': current_data.get('rain', {}).get('3h', 0)
            },
            'tomorrow': {
                'avg temp': tomorrow_data['main']['temp'],
                'max temp': tomorrow_data['main']['temp_max'],
                'min temp': tomorrow_data['main']['temp_min'],
                'rainFall': tomorrow_data.get('rain', {}).get('3h', 0)
            },
            'weekly': [
                {
                    'avg temp': day['main']['temp'],
                    'max temp': day['main']['temp_max'],
                    'min temp': day['main']['temp_min'],
                    'rainFall': day.get('rain', {}).get('3h', 0)
                }
                for day in weekly_data
            ],
            'raw': weatherData  # 원본 데이터도 유지
        }
        
        return processed
        
    except Exception as e:
        print(f'날씨 데이터 처리 중 오류 발생: {str(e)}')
        raise e 