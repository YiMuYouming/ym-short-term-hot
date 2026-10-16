"""三社区采集器的共享 HTTP 层。

两个约束决定了这里的写法：

1. **测试必须 100% 离线** —— 每个采集器的解析都是纯函数（吃 dict/HTML 字符串），
   HTTP 只是一个可注入的 `Fetcher`。离线测试直接传 lambda，不触网、不消耗配额。
2. **零重依赖** —— 只用标准库 `urllib`。雪球需要先访问首页拿匿名 cookie（`xq_a_token`、
   阿里云 WAF 的 `acw_tc`），所以这里带一个极简 CookieJar：它不追过期，但匿名 cookie
   在实测里能撑过一次会话。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from typing import Any, Callable, Mapping

# 一个 fetcher 就是一个 (url, headers) -> 文本 的函数；离线测试用 lambda 顶替
Fetcher = Callable[[str, Mapping[str, str]], str]


class FetchError(RuntimeError):
    """HTTP 层失败。采集器按「跳过该股并记账」处理，不让单股失败拖垮整轮。"""


@dataclass
class HttpClient:
    """基于 urllib 的极简客户端：一个会话、一个 cookie jar、可超时。"""

    timeout: float = 12.0
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    fetcher: Fetcher | None = None          # 注入后完全不走网络
    cookies: CookieJar = field(default_factory=CookieJar)
    failures: list[str] = field(default_factory=list)

    def _opener(self) -> urllib.request.OpenerDirector:
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def get(self, url: str, headers: Mapping[str, str] | None = None) -> str:
        """取一个 URL 的正文文本。注入 fetcher 时 headers 一并传给它。"""
        merged = {"User-Agent": self.user_agent, "Accept": "*/*"}
        merged.update(headers or {})
        if self.fetcher is not None:
            return self.fetcher(url, merged)
        request = urllib.request.Request(url, headers=merged)  # noqa: S310 - 目标域名固定在采集器内
        try:
            with self._opener().open(request, timeout=self.timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="replace")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise FetchError(f"{url}: {exc}") from exc

    def get_json(self, url: str, headers: Mapping[str, str] | None = None) -> Any:
        text = self.get(url, headers)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise FetchError(f"{url}: 返回不是 JSON（{exc}）") from exc

    def warm_up(self, url: str, headers: Mapping[str, str] | None = None) -> None:
        """预热：只为拿 cookie。失败不抛——调用方决定这算不算致命。"""
        try:
            self.get(url, headers)
        except FetchError as exc:
            self.failures.append(f"warm_up {url}: {exc}")

    def note_failure(self, what: str) -> None:
        self.failures.append(what)


def build_url(base: str, params: Mapping[str, Any] | None = None) -> str:
    """拼查询串；值为 None 的参数直接丢掉（各接口可选参数不同）。"""
    if not params:
        return base
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
    return f"{base}?{query}" if query else base
