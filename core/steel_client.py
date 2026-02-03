"""
Steel API Client - 云端浏览器服务集成
官方文档: https://docs.steel.dev
"""
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SteelSession:
    """Steel 浏览器会话"""
    id: str
    cdp_url: str
    session_viewer_url: str


class SteelClient:
    """Steel API 客户端"""

    BASE_URL = "https://api.steel.dev/v1"

    def __init__(self, api_key: str):
        """
        初始化 Steel 客户端

        Args:
            api_key: Steel API Key (格式: ste-...)
        """
        if not api_key or not api_key.startswith("ste-"):
            raise ValueError("Invalid Steel API Key format")

        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Steel-API-Key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    def create_session(
        self,
        headless: bool = True,
        dimensions: Optional[Dict[str, int]] = None,
        block_ads: bool = True,
        proxy: Optional[str] = None
    ) -> SteelSession:
        """
        创建 Steel 浏览器会话

        Args:
            headless: 无头模式
            dimensions: 窗口尺寸 {"width": 1920, "height": 1080}
            block_ads: 拦截广告
            proxy: 代理服务器

        Returns:
            SteelSession: 会话对象
        """
        payload: Dict[str, Any] = {}

        if dimensions:
            payload["dimensions"] = dimensions

        if block_ads:
            payload["blockAds"] = True

        if proxy:
            payload["proxy"] = proxy

        response = self.client.post("/sessions", json=payload)
        response.raise_for_status()

        data = response.json()
        session_id = data["id"]

        # 构建 CDP URL
        cdp_url = f"wss://connect.steel.dev?apiKey={self.api_key}&sessionId={session_id}"

        return SteelSession(
            id=session_id,
            cdp_url=cdp_url,
            session_viewer_url=data.get("sessionViewerUrl", "")
        )

    def release_session(self, session_id: str) -> None:
        """
        释放 Steel 浏览器会话

        Args:
            session_id: 会话 ID
        """
        response = self.client.delete(f"/sessions/{session_id}")
        response.raise_for_status()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话信息

        Args:
            session_id: 会话 ID

        Returns:
            会话详情
        """
        response = self.client.get(f"/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'client'):
            self.client.close()
