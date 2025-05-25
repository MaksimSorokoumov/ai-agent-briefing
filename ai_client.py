import requests
import json
import time
from typing import Optional, Dict, Any
from config import LM_STUDIO, SYSTEM_PROMPTS
from exceptions import AIConnectionError, InvalidResponseError
from logger import logger
from json_utils import robust_json_parse


class AIClient:
    """Клиент для работы с LM Studio"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or LM_STUDIO.base_url
        self.headers = {"Content-Type": "application/json"}
        self.max_retries = LM_STUDIO.max_retries
        self.timeout = LM_STUDIO.timeout
        logger.info(f"AI клиент инициализирован для работы с LM Studio: {self.base_url}")

    def make_request(self, prompt: str, system_prompt: str = None, 
                    max_tokens: int = 8192, temperature: float = 0.7) -> str:
        """Отправка запроса к LM Studio"""
        
        system_content = system_prompt or SYSTEM_PROMPTS["main"]
        
        payload = {
            "model": LM_STUDIO.default_model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Отправка запроса к AI (попытка {attempt + 1})")
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    logger.debug(f"Получен ответ от AI: {len(content)} символов")
                    return content
                else:
                    logger.warning(f"Ошибка API: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка подключения (попытка {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    
        error_msg = "Не удалось получить ответ от нейросети после всех попыток"
        logger.error(error_msg)
        raise AIConnectionError(error_msg)

    def check_connection(self) -> bool:
        """Проверка подключения к LM Studio"""
        try:
            response = requests.get(f"{self.base_url}/models", timeout=3)
            is_connected = response.status_code == 200
            logger.info(f"Проверка подключения к AI: {'успешно' if is_connected else 'неудачно'}")
            return is_connected
        except Exception as e:
            logger.warning(f"Ошибка при проверке подключения: {e}")
            return False

    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Парсинг JSON ответа с надежной обработкой"""
        result = robust_json_parse(response)
        if result is not None:
            logger.debug("JSON ответ успешно распарсен")
            return result
        else:
            logger.error(f"Не удалось распарсить JSON ответ")
            logger.error(f"Исходный ответ: {response}")
            raise InvalidResponseError("Не удалось распарсить JSON ответ после всех попыток")

    def _clean_json_response(self, text: str) -> str:
        """Очистка JSON ответа от обрамлений"""
        import re
        
        text = text.strip()
        
        # Убираем тройные ```
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        
        # Убираем префикс json после ```
        text = re.sub(r"^```\s*json", "", text, flags=re.IGNORECASE)
        
        # Извлекаем JSON объект или массив
        # Ищем либо объект {...}, либо массив [...]
        obj_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        arr_match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        
        if obj_match and arr_match:
            # Если есть и объект и массив, берем тот что начинается раньше
            if obj_match.start() < arr_match.start():
                return obj_match.group(0)
            else:
                return arr_match.group(0)
        elif obj_match:
            return obj_match.group(0)
        elif arr_match:
            return arr_match.group(0)
        else:
            return text 