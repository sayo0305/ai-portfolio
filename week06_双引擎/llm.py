# W6 双引擎封装 — 此后所有周统一经此调用
# 依赖：pip install openai requests python-dotenv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402 跨周导入 + 加载 .env

weekpath.load_env()

import requests  # noqa: E402
import openai  # noqa: E402


class LocalEngine:
    """本地引擎：Ollama http 直连（隐私任务优先、断网可用）"""
    def __init__(self, model=None):
        self.model = model or os.getenv("LOCAL_MODEL", "qwen2.5:0.5b")

    def ask(self, prompt, temperature=0.7, max_tokens=800):
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False}, timeout=60)
        r.raise_for_status()
        return r.json()["message"]["content"]


class APIEngine:
    """云端引擎：DeepSeek API（客户端按需创建，没密钥也能纯本地跑）"""
    def __init__(self):
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            self.client = openai.OpenAI(
                base_url="https://api.deepseek.com/v1",
                api_key=os.getenv("DEEPSEEK_API_KEY"))

    def ask(self, prompt, temperature=0.7, max_tokens=800):
        self._ensure_client()
        r = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature, max_tokens=max_tokens)
        return r.choices[0].message.content


class LLM:
    """统一入口，支持 prefer 参数切换与异常双向回退"""
    def __init__(self, local_model=None):
        self.local = LocalEngine(local_model)
        self.api = APIEngine()

    def ask(self, prompt, prefer="local", **kw):
        # 根据 prefer 决定首选引擎和备选引擎
        if prefer == "local":
            first, second, tag = self.local, self.api, "本地失败，自动切换云端"
        else:
            first, second, tag = self.api, self.local, "云端失败，自动切换本地"

        # ==== 作业1增强项：记录并打印首选引擎耗时 ====
        start_time = time.time()
        try:
            result = first.ask(prompt, **kw)
            elapsed = time.time() - start_time
            print("[%s] 耗时：%.2fs" % (first.__class__.__name__, elapsed))
            return result
        except Exception as e:
            print("[%s] %s" % (tag, e))
            
            # ==== 作业1增强项：记录并打印备选引擎耗时 ====
            start_time2 = time.time()
            result = second.ask(prompt, **kw)
            elapsed2 = time.time() - start_time2
            print("[%s] 耗时：%.2fs" % (second.__class__.__name__, elapsed2))
            return result


if __name__ == "__main__":
    # 测试一下
    llm = LLM()
    print("--- 测试本地引擎 ---")
    print(llm.ask("给《愚公移山》出一道 HSK4 阅读题", prefer="local"))