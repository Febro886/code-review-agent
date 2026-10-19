import os
import json
import time
import socket
import urllib.request
import urllib.error


class LLMClient:
    """统一的大模型客户端。

    支持 provider:
      - mock        : 无需网络/Key，靠规则模板输出，保证 MVP 可运行（满足 PPT 要求）
      - ollama      : 本地开源模型（Qwen2.5 / Llama3 等），完全免费、可离线
      - gemini      : Google Gemini 免费层（gemini-1.5-flash），有免费额度（境外）
      - groq        : Groq 免费额度（llama-3.1-8b-instant 等），速度极快（境外）
      - siliconflow : 硅基流动（国内可访问，OpenAI 兼容，注册送免费额度）
      - openai      : 任意 OpenAI 兼容端点（自定义 base_url）
    """

    def __init__(self, provider="mock", model=None, api_key=None, base_url=None, label=None):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv(self._key_env(provider))
        self.base_url = base_url
        # label 用于运行时友好展示「平台 / 模型」，便于区分三个不同 Agent 引擎
        self.label = label

    @staticmethod
    def _key_env(provider):
        return {
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
            "openai": "OPENAI_API_KEY",
        }.get(provider, "")

    def chat(self, system, user):
        if self.provider == "mock":
            # 真实生成由各 Agent 的 _mock 方法完成
            return None
        if self.provider == "ollama":
            return self._ollama(system, user)
        if self.provider == "gemini":
            return self._gemini(system, user)
        if self.provider == "groq":
            return self._groq(system, user)
        if self.provider in ("openai", "siliconflow"):
            return self._openai_compatible(system, user)
        raise ValueError(f"未知 provider: {self.provider}")

    def _post(self, url, payload, headers=None):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers=headers or {}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"调用 {self.provider} 失败（请检查网络/Key/本地服务）: {e}")

    def _ollama(self, system, user):
        url = self.base_url or "http://localhost:11434/api/generate"
        model = self.model or "qwen2.5:7b"
        prompt = f"{system}\n\n{user}"
        resp = self._post(url, {"model": model, "prompt": prompt, "stream": False})
        return resp.get("response", "").strip()

    def _gemini(self, system, user):
        model = self.model or "gemini-1.5-flash"
        if not self.api_key:
            raise RuntimeError("未配置 GEMINI_API_KEY 环境变量")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}
            ]
        }
        headers = {"Content-Type": "application/json"}
        resp = self._post(url, payload, headers)
        try:
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            return str(resp)

    def _groq(self, system, user):
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = self.model or "llama-3.1-8b-instant"
        if not self.api_key:
            raise RuntimeError("未配置 GROQ_API_KEY 环境变量")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = self._post(url, payload, headers)
        try:
            return resp["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            return str(resp)

    def _openai_compatible(self, system, user):
        # 兼容 OpenAI 协议的国内/国际免费平台：硅基流动(SiliconFlow)、DeepSeek 等
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        if not self.model:
            raise RuntimeError("openai/siliconflow provider 需要指定 model")
        if not self.api_key:
            env = self._key_env(self.provider) or "OPENAI_API_KEY"
            raise RuntimeError(f"未配置 {env} 环境变量")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        # 对超时 / 网络类错误自动重试（免费额度下偶发慢或抖动），其余错误直接抛出
        last_err = None
        for attempt in range(3):
            try:
                resp = self._post(url, payload, headers)
                return resp["choices"][0]["message"]["content"].strip()
            except Exception as e:  # noqa: BLE001
                last_err = e
                if isinstance(e, (urllib.error.URLError, socket.timeout)) or "timed out" in str(e).lower():
                    time.sleep(2 * (attempt + 1))
                    continue
                if isinstance(e, (KeyError, IndexError)):
                    return str(resp)
                raise
        raise last_err
