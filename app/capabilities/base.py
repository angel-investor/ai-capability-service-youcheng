"""capability 抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCapability(ABC):
    """所有 capability 的基类，子类需实现 run 方法"""

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        执行能力调用。

        Args:
            input_data: 请求中的 input 字段

        Returns:
            作为 data 字段的字典结果

        Raises:
            InvalidInputError: 输入参数不合法
            ModelAPIError: 调用模型 API 失败
        """
        ...
