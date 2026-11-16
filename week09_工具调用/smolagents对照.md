# W9 开源项目拆解加分作业（C 路径）

## 一、5行映射表（全员最低要求）

| 我写的 tool_agent.py | smolagents 里对应什么 |
| :--- | :--- |
| `TOOLS` 字典：名字 → 函数 | `@tool` 装饰器把带类型注解的函数变成 Tool，交给 `ToolCallingAgent(tools=[...])` |
| `SYS` 提示词要求输出 JSON | `ToolCallingAgent` 用模型原生 tool calling (JSON-like)，提示模板在 `prompts/toolcalling_agent.yaml` |
| `parse_calls` 剥围栏、兜底抓 JSON | 框架内部解析 `ChatMessageToolCall`，不用自己写正则 |
| `TOOLS[name](*args)` 执行 + 异常兜底 | 框架按 `Tool.inputs` 校验参数后调用，执行结果进入多步消息 |
| `run()` 手动回喂 + `max_calls` 收口 | `MultiStepAgent` 的多步循环由框架管理步数与停止条件 |

## 二、300字反思（手写循环 vs 框架各管了什么）

通过对照 smolagents 框架，我深刻体会到了“手写循环”与“成熟框架”的区别。

我手写的这 60 行循环，其实做了一个智能体最核心的三件事：**解析意图、执行工具、回喂结果**。但在这个过程中，我必须自己处理模型输出不规范的 Bug（比如剥掉 Markdown 围栏、写正则兜底），还要自己写代码校验参数类型（比如判断 `args` 是不是 list），并且要小心翼翼防着死循环。

而 smolagents 的 `ToolCallingAgent` 把这些脏活累活全接管了。它通过 `@tool` 装饰器强制要求类型注解和文档（约束即文档），由框架内部统一解析工具调用，用底层循环机制接管了 `max_calls` 收口。它甚至把“模型到底决定调什么”藏进了一层更深的抽象里。

这让我明白：框架替我们省去了大量工程校验与容错代码，让我们能专注于业务逻辑。但是，如果不先手写一遍，我就不懂框架在后台到底替我扛了多少雷。先手写再看框架，才知道自己真正掌控了什么、又让渡了什么控制权。