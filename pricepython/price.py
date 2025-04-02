import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import sys
import json
import os
from datetime import datetime, timedelta
import joblib

def create_price_predictor(crop_name):
    try:
        import numpy as np
        
        # 모델 디렉토리 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, 'models', crop_name)
        
        # 저장된 모델과 스케일러 로드
        model = joblib.load(os.path.join(model_dir, 'model.joblib'))
        scaler = joblib.load(os.path.join(model_dir, 'scaler.joblib'))
        
        # metadata에서 R2 score 읽기
        try:
            with open(os.path.join(model_dir, 'metadata.txt'), 'r', encoding='utf-8') as f:
                metadata = f.readlines()
                r2_score = float([line for line in metadata if 'R2 Score:' in line][0].split(':')[1].strip())
        except Exception as e:
            print(f"metadata 읽기 실패: {str(e)}")
            r2_score = 0.85  # 기본값
        
        # 모델의 특성 이름 확인 및 출력 (디버깅용)
        if hasattr(model, 'feature_names_in_'):
            print(f"{crop_name} 모델의 특성:", model.feature_names_in_)
        
        # 최근 데이터 로드
        latest_data = pd.read_csv(os.path.join(model_dir, 'latest_data.csv'))
        latest_data['date'] = pd.to_datetime(latest_data['date'])
        latest_price = latest_data[crop_name].iloc[0]
        
        def predict_prices(weather_data=None):
            try:
                predictions = {
                    'current': {},
                    'tomorrow': {},
                    'weekly': []
                }
                
                current_date = datetime.now()
                
                def prepare_prediction_data(target_date):
                    # metadata.txt에서 확인된 순서와 정확히 일치하는 특성 생성
                    features = [
                        'month', 'day', 'dayofweek', 'season',
                        'price_ma3', 'price_ma7', 'price_ma30',
                        'price_std3', 'price_std7', 'price_std30',
                        'price_change', 'price_change_ma7',
                        'month_sin', 'month_cos'
                    ]
                    
                    # 데이터 준비
                    new_data = pd.DataFrame({
                        'month': [target_date.month],
                        'day': [target_date.day],
                        'dayofweek': [target_date.weekday()],
                        'season': [1 if target_date.month in [3,4,5] else 2 if target_date.month in [6,7,8] 
                                else 3 if target_date.month in [9,10,11] else 4],
                        'price_ma3': [latest_price],
                        'price_ma7': [latest_price],
                        'price_ma30': [latest_price],
                        'price_std3': [latest_data[crop_name].head(3).std()],
                        'price_std7': [latest_data[crop_name].head(7).std()],
                        'price_std30': [latest_data[crop_name].head(30).std()],
                        'price_change': [0],
                        'price_change_ma7': [0],
                        'month_sin': [np.sin(2 * np.pi * target_date.month/12)],
                        'month_cos': [np.cos(2 * np.pi * target_date.month/12)]
                    })
                    
                    # 특성 순서 맞추기
                    new_data = new_data[features]
                    return scaler.transform(new_data)
                
                # 현재 가격 예측
                current_data = prepare_prediction_data(current_date)
                current_price = model.predict(current_data)[0]
                predictions['current'] = {
                    'price': round(current_price, 2),
                    'r2_score': r2_score
                }
                
                # 내일 가격 예측
                tomorrow_date = current_date + timedelta(days=1)
                tomorrow_data = prepare_prediction_data(tomorrow_date)
                tomorrow_price = model.predict(tomorrow_data)[0]
                predictions['tomorrow'] = {
                    'price': round(tomorrow_price, 2),
                    'r2_score': r2_score
                }
                
                # 주간 예측
                for i in range(2, 7):
                    future_date = current_date + timedelta(days=i)
                    future_data = prepare_prediction_data(future_date)
                    future_price = model.predict(future_data)[0]
                    predictions['weekly'].append({
                        'price': round(future_price, 2),
                        'r2_score': r2_score
                    })
                
                return predictions
                
            except Exception as e:
                print(f"예측 중 오류 발생: {str(e)}")
                return {"error": str(e)}
        
        return predict_prices
        
    except Exception as e:
        print(f"모델 로드 중 오류 발생: {str(e)}")
        return None

# 각 작물별 예측 함수 생성
predict_prices_dict = {
    'apple': create_price_predictor('apple'),
    'broccoli': create_price_predictor('broccoli'),
    'cabbage': create_price_predictor('cabbage'),
    'carrot': create_price_predictor('carrot'),
    'cucumber': create_price_predictor('cucumber'),
    'onion': create_price_predictor('onion'),
    'potato': create_price_predictor('potato'),
    'spinach': create_price_predictor('spinach'),
    'strawberry': create_price_predictor('strawberry'),
    'tomato': create_price_predictor('tomato')
}

def predict_prices(crop_name, weather_data=None):
    """
    작물 이름을 받아서 해당 작물의 가격을 예측하는 함수
    """
    if crop_name not in predict_prices_dict:
        return {"error": f"지원하지 않는 작물입니다: {crop_name}"}
    
    predictor = predict_prices_dict[crop_name]
    if predictor is None:
        return {"error": f"예측 모델을 생성할 수 없습니다: {crop_name}"}
    
    return predictor(weather_data)

if __name__ == "__main__":
    # 각 작물에 대한 예측 테스트
    for crop_name in predict_prices_dict.keys():
        try:
            print(f"\n=== {crop_name} 가격 예측 결과 ===")
            predictions = predict_prices(crop_name)
            if "error" not in predictions:
                print("\n현재 예측 가격:")
                print(f"가격: {predictions['current']['price']:,.0f}원")
                print(f"정확도: {predictions['current']['r2_score']:.2%}")
                
                print("\n내일 예측 가격:")
                print(f"가격: {predictions['tomorrow']['price']:,.0f}원")
                print(f"정확도: {predictions['tomorrow']['r2_score']:.2%}")
                
                print("\n주간 예측 가격:")
                for i, daily in enumerate(predictions['weekly'], 1):
                    print(f"{i+1}일 후: {daily['price']:,.0f}원 (정확도: {daily['r2_score']:.2%})")
            else:
                print(f"오류 발생: {predictions['error']}")
                
        except Exception as e:
            print(f"{crop_name} 예측 중 오류 발생: {str(e)}")
