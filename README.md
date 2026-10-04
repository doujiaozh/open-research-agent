Open Research Agent
===================

一个最小可用的研究型智能体：你给一个主题，它自己搜索、读网页、生成带来源的 Markdown 报告。
能在 Windows 7 + Python 3.11 上跑通。

快速开始
--------

pip install -r requirements.txt
copy .env.example .env
python cli/main.py research "固态电池最新进展"

查看历史：

python cli/main.py history

配置
----

.env 示例：

OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o-mini
MAX_STEPS=15
DB_PATH=./data/agent.db

常见后端：

- OpenAI 官方：https://api.openai.com/v1  模型 gpt-4o-mini
- DeepSeek：https://api.deepseek.com/v1  模型 deepseek-chat
- 硅基流动：https://api.siliconflow.cn/v1  模型 Qwen/Qwen2.5-7B-Instruct
- Kimi：https://api.moonshot.cn/v1  模型 moonshot-v1-8k

架构
----

cli/main.py            命令行入口
agent/loop.py          主循环：初始搜索 -> LLM 决策 -> 工具调用 -> 结束 -> 报告
agent/llm.py           LLM 调用（httpx 直调 OpenAI 兼容接口）
agent/tools/           工具集：web_search / fetch_url / read_file / write_file
agent/memory.py        SQLite 持久化
agent/safety.py        人工确认
agent/schema.py        Pydantic 数据模型

关键设计：

1. 初始搜索绕过 LLM：直接拿 goal 当 query，避免模型乱传参数
2. 决策和写报告分离：决策输出短 JSON，报告单独调用
3. JSON 解析容错：模型输出带 markdown 代码块也能解析
4. 工具调用白名单：危险工具（写文件）需人工确认

Windows 7 兼容性
----------------

本项目在 Windows 7 + Python 3.11 实测通过。注意事项：

1. 用 Python 3.11（3.12+ 不支持 Win7，3.8 太旧）
2. 必须用 pydantic 1.x：pip install "pydantic==1.10.13"
   原因：pydantic_core 是 Rust 编译，Win7 加载 DLL 失败
3. 不要用 openai SDK：依赖 jiter（Rust 编译），Win7 挂
4. 不要用 duckduckgo-search：依赖 primp（Rust 编译），Win7 挂
5. 不要用 typer：和现代 click 冲突
6. 别用 venv：某些精简版 Python 不带此模块
7. 代码里用 .dict() 不用 .model_dump()（pydantic 1.x 语法）

路线图
------

[x] v0.1.0 CLI 研究智能体，Bing 搜索，SQLite 记忆，Win7 兼容
[ ] v0.2.0 引用与去重
[ ] v0.3.0 Web UI
[ ] v0.4.0 长期记忆
[ ] v0.5.0 多智能体

License
-------

MIT