"""
AI Agent 增强模块（可选）

使用大语言模型提供更深入的调试建议。
需要 OpenAI API 密钥或其他 LLM 服务。
"""

import os
from typing import Dict, Optional


class AIDebugAgent:
    """
    AI 驱动的调试助手（可选增强功能）

    当启用时，使用 LLM 提供：
    1. 更详细的根因分析
    2. 代码级别的修复建议
    3. 与学生的对话式交互
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = 'openai'):
        """
        初始化 AI agent

        Args:
            api_key: API 密钥（可选，从环境变量读取）
            provider: 'openai', 'anthropic', 或 'local'
        """
        self.enabled = False
        self.provider = provider
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')

        if self.api_key:
            self.enabled = True
            self._init_client()

    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.provider == 'openai':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                print("✓ OpenAI AI Agent 已启用")
            except ImportError:
                print("⚠ 需要安装 openai: pip install openai")
                self.enabled = False

        elif self.provider == 'anthropic':
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                print("✓ Claude AI Agent 已启用")
            except ImportError:
                print("⚠ 需要安装 anthropic: pip install anthropic")
                self.enabled = False

    def enhance_analysis(self, basic_analysis: Dict, debug_output: str) -> Dict:
        """
        使用 AI 增强基础分析

        Args:
            basic_analysis: 基于规则的分析结果
            debug_output: 原始调试输出

        Returns:
            增强后的分析结果
        """
        if not self.enabled:
            return basic_analysis

        try:
            # 构建提示
            prompt = self._build_prompt(basic_analysis, debug_output)

            # 调用 LLM
            ai_insights = self._call_llm(prompt)

            # 合并结果
            enhanced = basic_analysis.copy()
            enhanced['ai_insights'] = ai_insights
            enhanced['ai_enabled'] = True

            return enhanced

        except Exception as e:
            print(f"AI 增强失败: {e}")
            return basic_analysis

    def _build_prompt(self, analysis: Dict, debug_output: str) -> str:
        """构建 LLM 提示"""

        # 提取关键信息
        hypotheses = analysis.get('hypotheses', [])
        findings = analysis.get('all_findings', [])

        prompt = f"""你是一个操作系统调试专家。学生遇到了内核崩溃，需要你的帮助。

## 调试输出
```
{debug_output[:2000]}  # 限制长度
```

## 自动分析结果
"""

        if hypotheses:
            prompt += "\n### 检测到的假设：\n"
            for i, hyp in enumerate(hypotheses[:3], 1):
                prompt += f"{i}. {hyp['scenario']} (优先级: {hyp['priority']})\n"

        if findings:
            prompt += "\n### 关键发现：\n"
            for finding in findings[:5]:
                prompt += f"- [{finding['severity']}] {finding['category']}\n"

        prompt += """

请提供：
1. **根本原因解释**（用学生能理解的语言）
2. **具体的代码修复建议**（如果可能，给出代码示例）
3. **调试步骤**（下一步应该做什么）
4. **学习要点**（这个 bug 教会了我们什么）

保持简洁、实用、教育性。
"""

        return prompt

    def _call_llm(self, prompt: str) -> Dict:
        """调用 LLM API"""

        if self.provider == 'openai':
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个操作系统调试专家助教。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            return {
                'explanation': response.choices[0].message.content,
                'model': 'gpt-4',
                'provider': 'openai'
            }

        elif self.provider == 'anthropic':
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                'explanation': response.content[0].text,
                'model': 'claude-3-5-sonnet',
                'provider': 'anthropic'
            }

        return {}

    def chat(self, message: str, context: Dict) -> str:
        """
        对话式调试助手

        允许学生提问并获得针对性回答
        """
        if not self.enabled:
            return "AI 对话功能未启用。请设置 API 密钥。"

        prompt = f"""基于以下调试上下文，回答学生的问题。

## 上下文
- 异常类型: {context.get('exception_type', 'Unknown')}
- 发现: {len(context.get('findings', []))} 个问题

## 学生问题
{message}

请提供清晰、教育性的回答。
"""

        try:
            result = self._call_llm(prompt)
            return result.get('explanation', '无法生成回答')
        except Exception as e:
            return f"对话出错: {e}"


# 单例实例（可选使用）
ai_agent = None

def get_ai_agent() -> AIDebugAgent:
    """获取全局 AI agent 实例"""
    global ai_agent
    if ai_agent is None:
        ai_agent = AIDebugAgent()
    return ai_agent


def enable_ai_enhancement() -> bool:
    """检查 AI 增强是否可用"""
    agent = get_ai_agent()
    return agent.enabled
