import re
from typing import List, Tuple
from openai import OpenAI
import logging
from functools import lru_cache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OpenAITranslator:
    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = 3
        self.timeout = 90

    def translate_batch(self, prompt: str, texts: List[str]) -> List[str]:
        """
        批量翻译文本列表。
        :param prompt: 提供给模型的系统提示。
        :param texts: 待翻译的文本列表。
        :return: 翻译结果列表，如果失败则返回 ["[TRANSLATION FAILED]"] * len(texts)。
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_retries}: Translating {len(texts)} texts...")
                response = self._call_openai(prompt, texts)
                parsed = self._parse_response(response, len(texts))
                if self._is_valid_translation(texts, parsed):
                    return parsed
            except Exception as e:
                logger.warning(f"Translation attempt {attempt} failed: {str(e)}")
        return texts 

    def _call_openai(self, prompt: str, texts: List[str]) -> str:
        """
        调用 OpenAI API 进行翻译。
        :param prompt: 系统提示。
        :param texts: 待翻译的文本列表。
        :return: API 返回的原始响应。
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": self._format_batch_input(texts)}
            ],
            temperature=0.0,
            timeout=self.timeout
        )
        return response.choices[0].message.content

    @staticmethod
    def _format_batch_input(texts: List[str]) -> str:
        """
        格式化输入，将文本列表转换为编号形式的字符串。
        :param texts: 文本列表。
        :return: 格式化后的字符串。
        """
        return "\n".join(f"{idx}. {text}" for idx, text in enumerate(texts, 1))

    @staticmethod
    def _parse_response(response: str, expected_length: int) -> List[str]:
        """
        解析 API 响应，提取翻译结果。
        :param response: API 返回的原始响应。
        :param expected_length: 期望的翻译结果数量。
        :return: 翻译结果列表，如果解析失败则返回 ["[PARSE ERROR]"] * expected_length。
        """
        # 移除 </think> 标记前的内容
        response = re.split(r"</think>", response, 1)[-1].strip()

        # 提取编号行的内容
        parsed_lines = []
        for line in response.split("\n"):
            match = re.match(r"^\d+\.\s*(.*)", line)
            if match:
                parsed_lines.append(match.group(1).strip())

        # 如果解析结果不完整，填充错误标记
        if len(parsed_lines) < expected_length:
            logger.warning(f"Parsing incomplete. Expected {expected_length}, got {len(parsed_lines)}.")
            return parsed_lines + ["[PARSE ERROR]"] * (expected_length - len(parsed_lines))
        return parsed_lines[:expected_length]

    @staticmethod
    def _is_valid_translation(texts: List[str], parsed: List[str]) -> bool:
        """
        验证翻译结果是否有效。
        :param texts: 原始文本列表。
        :param parsed: 解析后的翻译结果列表。
        :return: 是否有效。
        """
        if len(parsed) != len(texts):
            logger.warning(f"Validation failed: Translation length mismatch. "
                           f"Expected {len(texts)}, got {len(parsed)}.")
            return False
        return True
