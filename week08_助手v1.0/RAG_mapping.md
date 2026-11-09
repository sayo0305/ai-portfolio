# 官方 RAG 流水线 ↔ 我的 rag_qa.py 映射表

1. **Load + Split 加载与分块** -> `TextLoader` + `RecursiveCharacterTextSplitter(500/50)`，读取 HSK 等级标准节选。
2. **Embed + Store 向量化入库** -> `OllamaEmbeddings(nomic-embed-text)` + `Chroma` 本地持久化，数据不出本机。
3. **Retrieve 检索** -> `retrieve()` 取 top-k；`use_rag=True` 时先查资料再答。
4. **Prompt + Generate 拼词与生成** -> `build_prompt()` 拼 `SYSTEM_HINT + 资料 + 问题`，交 `LLM().ask(prefer=...)`。
5. **Deploy + Evaluate 部署与评估** -> W7 幻觉对照表是最朴素的评估；W15 再用 Streamlit 发布。