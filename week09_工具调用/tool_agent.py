# W9 手写最小工具调用循环（不用框架）
# 包含 4 个工具：get_time, calc, hsk_level, evaluate_text
import os
import csv
import sys
import ast
import json
import re
import operator
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

import openai  # noqa: E402

VOCAB = weekpath.data_path("生词表.csv")

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY，请先在 .env 中填写")
        _client = openai.OpenAI(base_url="https://api.deepseek.com/v1", api_key=key)
    return _client


def get_time():
    return str(datetime.datetime.now())


# ---- 安全计算：白名单 AST，绝不使用裸 eval ----
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只允许数字与 + - * / ** % 运算")


def calc(expr):
    """教学演示用：只做四则运算。为什么不用 eval？
    因为 eval 会执行任意 Python 代码，是典型的安全反模式（本课程伦理红线之一）。"""
    try:
        return str(_eval_node(ast.parse(str(expr), mode="eval")))
    except ZeroDivisionError:
        return "错误：除数为 0"
    except Exception as e:
        return "拒绝计算：%s" % e


def hsk_level(word):
    with open(VOCAB, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["词汇"].strip() == str(word).strip():
                return "%s 是 %s 级" % (word, row["HSK等级"])
    return "未找到 %s" % word


# ==== 第 4 个工具：课文难度评估 ====
def evaluate_text(text, target_level="4"):
    """评估一段课文的难度（超纲词统计）"""
    words_in_db = {}
    try:
        with open(VOCAB, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                words_in_db[row["词汇"].strip()] = row["HSK等级"].strip()
    except Exception:
        pass

    out_of_syllabus = []
    for char in str(text):
        # 如果字在生词表里，且等级高于目标等级
        if char in words_in_db and words_in_db[char] > str(target_level):
            out_of_syllabus.append(char)

    unique_out = list(set(out_of_syllabus))
    if not unique_out:
        return f"评估结果：课文符合 HSK {target_level} 级水平，没有超纲词。"
    else:
        return f"评估结果：课文有 {len(unique_out)} 个超纲词，分别是：{', '.join(unique_out)}"


# 把 4 个工具放进字典
TOOLS = {
    "get_time": get_time, 
    "calc": calc, 
    "hsk_level": hsk_level, 
    "evaluate_text": evaluate_text
}

# 提示词
SYS = ("你是国际中文助教。可用工具只有这4个：get_time（查当前时间，无参数）、"
       "calc（四则运算，如 calc('35*24')）、hsk_level（查生词 HSK 等级，如 hsk_level('把')）、"
       "evaluate_text（评估课文难度，参数为课文内容和目标等级，如 evaluate_text('今天天气真好', '4')）。"
       '如需调用，只输出一行 JSON，格式：{"tool": "工具名", "args": [参数]}；'
       "一次可以输出一个或多个工具调用；无需工具时直接回答。")


def parse_calls(txt):
    """容错解析：支持一次解析出多个工具调用"""
    s = (txt or "").strip()
    s = s.replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, dict): return [obj]
        if isinstance(obj, list): return obj
    except Exception:
        pass
    
    calls = []
    for blk in re.findall(r"\{[^}]*\}", s):
        try:
            obj = json.loads(blk)
            if isinstance(obj, dict):
                calls.append(obj)
        except Exception:
            continue
    return calls


def run(user_msg, max_calls=2):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]
    for _ in range(max_calls):
        txt = get_client().chat.completions.create(
            model="deepseek-chat", messages=msgs).choices[0].message.content
        
        calls = [c for c in parse_calls(txt) if isinstance(c.get("tool"), str) and c.get("tool") in TOOLS]
        
        if not calls:
            return txt  # 没调用工具，直接回答
            
        results = []
        for call in calls:
            args = call.get("args") or []
            if not isinstance(args, list):
                results.append("工具参数格式错误：%r" % (args,))
                continue
            try:
                res = TOOLS[call["tool"]](*args)
                results.append("%s%r → %s" % (call["tool"], args, res))
            except Exception as e:
                results.append("工具执行失败：%s" % e)
                
        msgs += [{"role": "assistant", "content": txt},
                 {"role": "user", "content": "工具返回：%s。请据此作答。" % "；".join(results)}]
                 
    return get_client().chat.completions.create(
        model="deepseek-chat", messages=msgs).choices[0].message.content


if __name__ == "__main__":
    # 换成更自然、更像真实教学场景的测试问句
    q = (
        "我是国际中文老师，现在正在备课。请帮我做三件事：\n"
        "1. 帮我查一下，如果一份试卷满分是 120 分，某学生考了 96 分，折算成百分制是多少分？\n"
        "2. 看看现在备课到几点了？\n"
        "3. 我想用这段课文作为 HSK 4 级的阅读材料：'虽然天气很恶劣，但他依然坚持不懈地完成任务。' 帮我评估一下难度，有没有超纲词？\n"
        "4. 顺便查一下，“坚持”这个词是几级词汇？"
    )
    print("用户输入：\n", q)
    print("=" * 50)
    print("助手：\n", run(q))