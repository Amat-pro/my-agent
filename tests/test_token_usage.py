"""Token usage 计量测试。"""

from app.observability.token_usage.base import ApproximateTokenCounter


def test_approximate_token_counter_counts_words_and_cjk_characters() -> None:
    """近似计数器在无 provider SDK 时提供稳定的本地估算。"""
    counter = ApproximateTokenCounter()

    assert counter.count_text("hello world") == 2
    assert counter.count_text("你好") == 2
    assert counter.count_text("hello 世界") == 3


def test_approximate_token_counter_returns_zero_for_blank_text() -> None:
    """空白文本不应增加 token 使用量。"""
    counter = ApproximateTokenCounter()

    assert counter.count_text("   ") == 0
