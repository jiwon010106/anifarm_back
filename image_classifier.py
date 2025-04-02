import torch
import onnxruntime
import numpy as np
from torchvision import transforms
import io
from PIL import Image
import requests
import tensorflow as tf
import logging
from pydantic import BaseModel
from typing import Dict, Optional
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 모델 응답을 위한 Pydantic 모델
class ImageClassificationResponse(BaseModel):
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    message: Optional[str] = None

class ImageClassifier:
    def __init__(self):
        self.kiwi_session = self._load_kiwi_model()
        self.chamoe_session = self._load_chamoe_model()
        self.plant_session = self._load_plant_model()
        self.strawberry_session = self._load_strawberry_model()
        self.apple_session = self._load_apple_model()
        self.potato_session = self._load_potato_model()
        self.tomato_session = self._load_tomato_model()
        self.grape_session = self._load_grape_model()
        self.corn_session = self._load_corn_model()
        
        # 클래스 레이블 정의
        self.kiwi_labels = {
            0: "잎_점무늬병",
            1: "잎_정상",
            2: "잎_총채벌레"
        }
        
        self.chamoe_labels = {
            0: "노균병",
            1: "정상",
            2: "흰가루병"
        }
        
        self.plant_labels = {
            0: "비식물",
            1: "식물"
        }

        self.strawberry_labels = {
            0: "딸기 잎끝마름",
            1: "정상"
        }

        self.apple_labels = {
            0: "사과 검은무늬병",
            1: "사과 흑색 부패병",
            2: "사과 삼나무 녹병",
            3: "정상"
        }

        self.potato_labels = {
            0: "감자 잎마름병",
            1: "감자 역병",
            2: "정상"
        }

        self.tomato_labels = {
            0: "토마토 박테리아성 반점병",
            1: "토마토 잎마름병",
            2: "토마토 역병",
            3: "토마토 잎곰팡이병",
            4: "토마토 세프토이라 잎반점병",
            5: "토마토 거미 진드기 피해",
            6: "토마토 표적반점병",
            7: "토마토 황화 잎말림 바이러스",
            8: "토마토 모자이크 바이러스",
            9: "정상"
        }

        self.grape_labels = {
            0: "포도 에스카병",
            1: "포도 흑색 부패병",
            2: "포도 잎마름병",
            3: "정상"
        }

        self.corn_labels = {
            0: "옥수수 세르코스포라 잎반점병",
            1: "옥수수 일반 녹병",
            2: "옥수수 북부 잎마름병",
            3: "정상"
        }
              

    def _load_kiwi_model(self):
        try:
            url = "https://huggingface.co/jjiw/densenet161-onnx/resolve/main/model.onnx"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            return onnxruntime.InferenceSession(model_bytes.getvalue())
        except Exception as e:
            logger.error(f"키위 모델 로드 실패: {str(e)}")
            return None

    def _load_chamoe_model(self):
        try:
            url = "https://huggingface.co/jjiw/disease-classifier-onnx/resolve/main/model.onnx"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            return onnxruntime.InferenceSession(model_bytes.getvalue())
        except Exception as e:
            logger.error(f"참외 모델 로드 실패: {str(e)}")
            return None

    def _load_plant_model(self):
        try:
            url = "https://huggingface.co/jjiw/plant-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "temp_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"식물 분류 모델 로드 실패: {str(e)}")
            return None

    def _load_strawberry_model(self):
        try:
            url = "https://huggingface.co/ro981009/strawberry-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "strawberry_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"딸기 모델 로드 실패: {str(e)}")
            return None

    def _load_apple_model(self):
        try:
            url = "https://huggingface.co/ro981009/apple-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "apple_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"사과 모델 로드 실패: {str(e)}")
            return None

    def _load_potato_model(self):
        try:
            url = "https://huggingface.co/ro981009/potato-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "potato_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"감자 모델 로드 실패: {str(e)}")
            return None

    def _load_tomato_model(self):
        try:
            url = "https://huggingface.co/ro981009/tomato-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "tomato_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"토마토 모델 로드 실패: {str(e)}")
            return None

    def _load_grape_model(self):
        try:
            url = "https://huggingface.co/ro981009/grape-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "grape_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"포도 모델 로드 실패: {str(e)}")
            return None

    def _load_corn_model(self):
        try:
            url = "https://huggingface.co/ro981009/corn-classifier-h5/resolve/main/model.h5"
            response = requests.get(url)
            model_bytes = io.BytesIO(response.content)
            temp_model_path = "corn_model.h5"
            with open(temp_model_path, "wb") as f:
                f.write(model_bytes.getvalue())
            model = tf.keras.models.load_model(temp_model_path)
            os.remove(temp_model_path)
            return model
        except Exception as e:
            logger.error(f"옥수수 모델 로드 실패: {str(e)}")
            return None


    def preprocess_image(self, image, target_size=(224, 224)):
        """공통 이미지 전처리 함수"""
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image = image.resize(target_size)
        return image

    async def classify_kiwi(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.kiwi_session is None:
                raise ValueError("키위 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                  std=[0.229, 0.224, 0.225])
            ])
            img_tensor = transform(image).numpy()

            input_name = self.kiwi_session.get_inputs()[0].name
            outputs = self.kiwi_session.run(None, 
                {input_name: img_tensor.reshape(1, 3, 224, 224)})
            probabilities = torch.nn.functional.softmax(torch.tensor(outputs[0][0]), dim=0)
            
            predicted_idx = probabilities.argmax().item()
            confidence = float(probabilities[predicted_idx])

            class_probs = {
                self.kiwi_labels[i]: float(probabilities[i])
                for i in range(len(self.kiwi_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.kiwi_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="키위 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"키위 분류 오류: {str(e)}")
            raise

    async def classify_chamoe(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.chamoe_session is None:
                raise ValueError("참외 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            input_name = self.chamoe_session.get_inputs()[0].name
            outputs = self.chamoe_session.run(None, {input_name: img_array})
            probabilities = torch.nn.functional.softmax(torch.tensor(outputs[0][0]), dim=0)
            
            predicted_idx = probabilities.argmax().item()
            confidence = float(probabilities[predicted_idx])

            class_probs = {
                self.chamoe_labels[i]: float(probabilities[i])
                for i in range(len(self.chamoe_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.chamoe_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="참외 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"참외 분류 오류: {str(e)}")
            raise

    async def classify_plant(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.plant_session is None:
                raise ValueError("식물 분류 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.plant_session.predict(img_array)
            confidence = float(predictions[0][0])
            predicted_idx = 1 if confidence > 0.5 else 0

            class_probs = {
                "비식물": float(confidence),
                "식물": float(1 - confidence)
            }

            return ImageClassificationResponse(
                predicted_class=self.plant_labels[predicted_idx],
                confidence=confidence if predicted_idx == 1 else 1 - confidence,
                class_probabilities=class_probs,
                message="식물 분류가 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"식물 분류 오류: {str(e)}")
            raise

    async def classify_strawberry(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.strawberry_session is None:
                raise ValueError("딸기 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.strawberry_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.strawberry_labels[i]: float(predictions[0][i])
                for i in range(len(self.strawberry_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.strawberry_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="딸기 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"딸기 분류 오류: {str(e)}")
            raise

    async def classify_apple(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.apple_session is None:
                raise ValueError("사과 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.apple_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.apple_labels[i]: float(predictions[0][i])
                for i in range(len(self.apple_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.apple_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="사과 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"사과 분류 오류: {str(e)}")
            raise

    async def classify_potato(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.potato_session is None:
                raise ValueError("감자 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.potato_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.potato_labels[i]: float(predictions[0][i])
                for i in range(len(self.potato_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.potato_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="감자 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"감자 분류 오류: {str(e)}")
            raise

    async def classify_tomato(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.tomato_session is None:
                raise ValueError("토마토 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.tomato_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.tomato_labels[i]: float(predictions[0][i])
                for i in range(len(self.tomato_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.tomato_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="토마토 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"토마토 분류 오류: {str(e)}")
            raise

    async def classify_grape(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.grape_session is None:
                raise ValueError("포도 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = self.grape_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.grape_labels[i]: float(predictions[0][i])
                for i in range(len(self.grape_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.grape_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="포도 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"포도 분류 오류: {str(e)}")
            raise

    async def classify_corn(self, image: Image.Image) -> ImageClassificationResponse:
        try:
            if self.corn_session is None:
                raise ValueError("옥수수 모델이 로드되지 않았습니다")

            image = self.preprocess_image(image)
            img_array = np.array(image).astype('float32') / 255.0
            img_array = np.expand_dims(img_array, axis=0)   

            predictions = self.corn_session.predict(img_array)
            predicted_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_idx])

            class_probs = {
                self.corn_labels[i]: float(predictions[0][i])
                for i in range(len(self.corn_labels))
            }

            return ImageClassificationResponse(
                predicted_class=self.corn_labels[predicted_idx],
                confidence=confidence,
                class_probabilities=class_probs,
                message="옥수수 질병 분석이 완료되었습니다"
            )

        except Exception as e:
            logger.error(f"옥수수 분류 오류: {str(e)}")
            raise

# 싱글톤 인스턴스 생성
classifier = ImageClassifier() 