import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

def get_satellite_data():
    # .env 파일 로드
    load_dotenv()
    
    # API 엔드포인트 URL
    url = "http://apis.data.go.kr/1360000/SatlitImgInfoService/getInsightSatlit"
    
    # API 요청 파라미터
    params = {
        "serviceKey": os.getenv('DATADECODING_API_KEY'),  # 디코딩된 API 키 사용
        "pageNo": "1",
        "numOfRows": "10",
        "dataType": "JSON",
        "sat": "G2",  # 천리안위성 2A호
        "data": "vi006",  # 가시영상
        "area": "ko",  # 한반도 영역
        "time": datetime.now().strftime('%Y%m%d')  # YYYYMMDD 형식
    }

    try:
        # API 호출
        response = requests.get(url, params=params)
        
        # 응답 내용 출력 (디버깅용)
        print("Response status:", response.status_code)
        print("Response content:", response.text)
        
        response.raise_for_status()  # HTTP 에러 체크
        
        # JSON 응답 파싱
        data = response.json()
        
        # 데이터 구조 확인 및 반환
        if "response" in data and "body" in data["response"] and "items" in data["response"]["body"]:
            return data
        else:
            print("위성 데이터 구조가 올바르지 않습니다:", data)
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"위성영상 API 호출 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
        return None

def get_price_data():
    # .env 파일 로드
    load_dotenv()
    
    # 오늘 날짜 가져오기 (YYYY-MM-DD 형식)
    today = datetime.now().strftime('%Y-%m-%d')
    
    # API 엔드포인트 URL
    url = "http://www.kamis.or.kr/service/price/xml.do"
    
    # 채소류와 곡물류 데이터를 저장할 리스트
    all_data = {"data": {"item": []}}

    # 채소류(200)와 곡물류(100) 카테고리 코드
    categories = [
        {"code": "200", "name": "채소류"},
        {"code": "100", "name": "곡물류"}
    ]
    
    try:
        for category in categories:
            # API 요청 파라미터
            params = {
                "action": "dailyPriceByCategoryList",
                "p_product_cls_code": "02",
                "p_country_code": "1101",
                "p_regday": today,
                "p_convert_kg_yn": "N",
                "p_item_category_code": category["code"],
                "p_cert_key": os.getenv('KAMIS_API_KEY'),
                "p_cert_id": "5243",
                "p_returntype": "json"
            }

            # API 호출
            response = requests.get(url, params=params)
            response.raise_for_status()  # HTTP 에러 체크
            
            # JSON 응답 파싱
            data = response.json()
            
            # 카테고리 정보 추가
            if "data" in data and "item" in data["data"]:
                for item in data["data"]["item"]:
                    item["category_code"] = category["code"]
                    item["category_name"] = category["name"]
                    all_data["data"]["item"].append(item)
        
        return all_data
        
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    satellite_data = get_satellite_data()
    if satellite_data:
        print(json.dumps(satellite_data, indent=2, ensure_ascii=False))
    get_price_data()