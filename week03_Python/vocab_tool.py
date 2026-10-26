# W3 生词表 CSV -> 自动生成练习题
# 运行: python vocab_tool.py
import os
import sys  # 引入系统模块，用于处理路径
import csv
from collections import Counter  # 官方教程学到的统计写法

# 将项目根目录加入系统路径，确保无论在哪里运行都能找到 weekpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weekpath  # 统一解析 data/ 路径，换目录也不会找不到文件

DATA = weekpath.data_path("生词表.csv")

def load_words(path=DATA):
    """读取CSV数据"""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def filter_by_level(words, level="4"):
    """按HSK等级筛选词汇"""
    return [w for w in words if str(w["HSK等级"]) == str(level)]

def count_by_pos(words):
    """统计词性分布（使用官方推荐的 Counter 写法）"""
    return Counter(w["词性"] for w in words)

def gen_exercises(words, out=None):
    """生成练习题文件（包含造句题和填空题）"""
    out = out or weekpath.root_path("练习.txt")
    # 加上 newline='' 和 encoding='utf-8-sig' 防止Windows下乱码和不换行
    with open(out, "w", encoding="utf-8-sig", newline='') as f:
        for w in words:
            # 题型1：造句题
            f.write("用“%s”造一个句子。（%s）\r\n" % (w["词汇"], w["词性"]))
            # 题型2：填空题（把词语抠掉，变成下划线）
            f.write("填空：____ 意思是指“%s”。（%s）\r\n" % (w["释义"], w["词性"]))
            # 加一个空行，让不同词的题目隔开
            f.write("\r\n")

if __name__ == "__main__":
    # 1. 读取数据
    words = load_words()
    
    # 2. 筛选数据（先定义目标等级，方便以后修改）
    target_level = "4" 
    lv4 = filter_by_level(words, target_level)
    
    # 3. 打印统计信息（Counter 的结果与原来的字典完全一致）
    print("总词汇 %d 个，其中 HSK%s 词汇 %d 个，词性分布: %s" 
          % (len(words), target_level, len(lv4), count_by_pos(lv4)))
    
    # 4. 生成文件
    out_path = weekpath.root_path("练习.txt")
    gen_exercises(lv4, out_path)
    
    print("已生成: %s" % out_path)