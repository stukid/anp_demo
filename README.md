# anp_demo

这是个简化版的 ANP demo, 主要用来展示 Agent 在运行过程中是怎样使用 ANP 协议来递归爬取 URL，以及使用 LLM 来找到对应的接口，并成功调用。

## 创建虚拟环境
``` bash
python -m venv .venv
source .venv/bin/activate
```

## 安装依赖
``` bash
uv pip install -r src/anp_demo/backend/requirements.txt
```

## 启动
``` bash
python -m src.anp_demo.backend.anp_examples_backend
```

浏览器访问 http://localhost:5000

## 交互

按示例输入想问的问题，然后提交问题，右下角将实时显示背后的调用过程，帮助新的开发者理解 ANP。 