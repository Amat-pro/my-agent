"""Token 使用量计数接口与本地估算实现。

本模块只提供可替换的 token 计数边界。真实模型接入后，可以用 provider 返回的
usage 或专用 tokenizer 替换当前估算实现。
"""

import re
from typing import Protocol


class TokenCounter(Protocol):
    """Token 计数接口。"""

    def count_text(self, text: str) -> int:
        """返回文本的 token 数估算值。"""


class ApproximateTokenCounter:
    """不依赖外部 tokenizer 的确定性估算器。

    英文和数字按连续单词计数，CJK 字符按单字计数。该实现只用于本地开发和
    Runtime 观测占位，不代表真实模型账单。
    """

    _token_pattern = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")

    def count_text(self, text: str) -> int:
        """按稳定规则估算文本 token 数。"""
        if not text.strip():
            return 0
        return len(self._token_pattern.findall(text))
