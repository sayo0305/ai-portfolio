import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weekpath
weekpath.load_env()

from week04_API.week4_api_bot import ask

q = "用一句话说明什么是把字句"

print("=== temperature=0.0 ===")
print(ask(q, temperature=0.0, max_tokens=800))

print("\n=== temperature=1.5 ===")
print(ask(q, temperature=1.5, max_tokens=800))

print("\n=== max_tokens=15 ===")
print(ask(q, temperature=0.7, max_tokens=15))

print("\n=== max_tokens=800 ===")
print(ask(q, temperature=0.7, max_tokens=800))