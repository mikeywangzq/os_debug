# 🤖 AI 增强功能设置指南

OS 调试助手支持**可选的 AI 增强**功能，可以提供更深入的分析和建议。

## 🎯 AI vs 基于规则的分析

### 基于规则的分析（默认）
✅ **优势**：
- 快速响应（毫秒级）
- 完全离线工作
- 零成本
- 结果可预测
- 适合教学

### AI 增强分析（可选）
🚀 **额外优势**：
- 更深入的根因解释
- 代码级别的修复建议
- 更灵活的推理能力
- 处理未知场景

## 📦 安装步骤

### 方式 1：使用 OpenAI GPT-4

**步骤 1：安装依赖**
```bash
pip install openai
```

**步骤 2：设置 API 密钥**
```bash
# Linux/Mac
export OPENAI_API_KEY="sk-your-api-key-here"
export ENABLE_AI=true

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:ENABLE_AI="true"

# Windows CMD
set OPENAI_API_KEY=sk-your-api-key-here
set ENABLE_AI=true
```

**步骤 3：启动服务器**
```bash
cd backend
python app.py
```

你应该看到：
```
✓ OpenAI AI Agent 已启用
AI Enhancement: Enabled ✓
```

### 方式 2：使用 Anthropic Claude

**步骤 1：安装依赖**
```bash
pip install anthropic
```

**步骤 2：修改代码**
在 `backend/app.py` 中修改：
```python
# 在初始化 engine 时指定 provider
engine = HypothesisEngine(enable_ai=ENABLE_AI, ai_provider='anthropic')
```

在 `backend/analyzers/hypothesis_engine.py` 中修改：
```python
def __init__(self, enable_ai: bool = False, ai_provider: str = 'openai'):
    # ...
    if enable_ai and AI_AVAILABLE:
        self.ai_agent = AIDebugAgent(provider=ai_provider)
```

**步骤 3：设置 API 密钥**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
export ENABLE_AI=true
```

## 💰 成本估算

### OpenAI GPT-4
- 输入：$0.03 / 1K tokens
- 输出：$0.06 / 1K tokens
- 每次分析约：$0.01 - $0.05

### Anthropic Claude 3.5 Sonnet
- 输入：$0.003 / 1K tokens
- 输出：$0.015 / 1K tokens
- 每次分析约：$0.001 - $0.01

💡 **建议**：对于教育用途，可以设置每月预算限制。

## 🔧 高级配置

### 创建配置文件

创建 `backend/.env` 文件：
```bash
# AI 设置
ENABLE_AI=true
OPENAI_API_KEY=sk-your-key-here

# 或使用 Claude
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# 服务器设置
PORT=5000
DEBUG=true
```

然后使用 python-dotenv：
```bash
pip install python-dotenv
```

在 `backend/app.py` 开头添加：
```python
from dotenv import load_dotenv
load_dotenv()
```

### 自定义 AI 提示

编辑 `backend/analyzers/ai_agent.py` 中的 `_build_prompt` 方法来自定义 AI 的行为。

## 🧪 测试 AI 功能

```python
# 创建测试脚本 test_ai.py
import os
os.environ['ENABLE_AI'] = 'true'
os.environ['OPENAI_API_KEY'] = 'your-key'

from analyzers.hypothesis_engine import HypothesisEngine

engine = HypothesisEngine(enable_ai=True)

test_input = """
scause 0x000000000000000d
stval 0x0000000000000000
#0 panic() at kernel.c:127
"""

result = engine.analyze(test_input)

if result.get('ai_enabled'):
    print("✓ AI 增强已激活")
    print("\nAI 见解:")
    print(result['ai_insights']['explanation'])
else:
    print("✗ AI 未激活")
```

## 🎓 教学环境部署

### 选项 1：为所有学生启用
设置环境变量后启动服务器，所有学生共享 API 密钥。

**优点**：
- 学生无需配置
- 统一体验

**缺点**：
- 成本由课程承担
- 需要设置使用限制

### 选项 2：学生自己配置
让学生使用自己的 API 密钥。

**优点**：
- 零成本给课程
- 学生学习 AI API 使用

**缺点**：
- 配置复杂度
- 体验不统一

## 🔒 安全注意事项

⚠️ **重要**：
1. 永远不要将 API 密钥提交到 Git
2. 使用 `.gitignore` 排除 `.env` 文件
3. 为生产环境设置使用限制
4. 定期轮换 API 密钥

## ❓ 常见问题

**Q: 没有 API 密钥可以使用吗？**
A: 可以！不设置 API 密钥时，工具使用基于规则的分析，功能完全正常。

**Q: AI 分析会替代基于规则的分析吗？**
A: 不会。AI 增强是**补充**而非替代。你会同时获得两种分析结果。

**Q: 支持本地 LLM 吗？**
A: 理论上支持。你可以修改 `ai_agent.py` 来使用 Ollama 等本地模型。

**Q: 分析速度会变慢吗？**
A: AI 增强会增加 1-3 秒延迟。基于规则的分析仍然即时返回。

## 📚 下一步

- 尝试不同的 AI 模型
- 自定义提示词以匹配课程内容
- 收集学生反馈优化 AI 行为
- 考虑集成本地模型以降低成本

---

**需要帮助？** 查看 [GitHub Issues](https://github.com/yourusername/os_debug/issues) 或查阅文档。
