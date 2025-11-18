# 📚 OS 调试助手 - 文档中心

欢迎来到 OS 调试助手的文档中心！这里包含了所有技术文档、使用指南和教程。

---

## 📖 文档索引

### 🚀 快速开始

| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [../README.md](../README.md) | 项目总览、安装指南、快速开始 | 所有用户 |
| [GDB_INTEGRATION_GUIDE.md](GDB_INTEGRATION_GUIDE.md) | v2.0 实时 GDB 集成使用指南 | 调试用户 |

### 🏗️ 技术文档

| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [GDB_INTEGRATION_DESIGN.md](GDB_INTEGRATION_DESIGN.md) | v2.0 实时 GDB 技术设计 | 开发者 |

### 📝 其他资源

| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [../AI_SETUP.md](../AI_SETUP.md) | AI 增强功能配置指南 | 高级用户 |
| [../TESTING.md](../TESTING.md) | 测试报告和 Bug 修复记录 | 开发者 |
| [../V2_PLAN.md](../V2_PLAN.md) | v2.0 开发计划和路线图 | 贡献者 |
| [../V2.0_RELEASE_NOTES.md](../V2.0_RELEASE_NOTES.md) | v2.0 完整发布说明 | 所有用户 |

---

## 🎯 按需求查找

### 我想快速上手

1. 阅读 [主 README](../README.md) 的"快速开始"部分
2. 按照步骤安装并启动服务器
3. 尝试加载示例或粘贴你的调试输出

### 我想使用实时 GDB 调试

1. 阅读 [GDB 集成使用指南](GDB_INTEGRATION_GUIDE.md)
2. 按照"快速开始"教程连接 GDB
3. 查看"典型使用场景"学习最佳实践

### 我想启用 AI 增强

1. 阅读 [AI 配置指南](../AI_SETUP.md)
2. 获取 OpenAI 或 Anthropic API 密钥
3. 设置环境变量并重启服务器

### 我想了解技术实现

1. 阅读 [GDB 技术设计文档](GDB_INTEGRATION_DESIGN.md)
2. 查看系统架构图和数据流
3. 参考 API 文档了解各模块接口

### 我想贡献代码

1. 阅读 [测试报告](../TESTING.md) 了解测试方法
2. 查看 [v2.0 计划](../V2_PLAN.md) 了解开发路线图
3. Fork 仓库并提交 Pull Request

---

## 📊 文档结构

```
os_debug/
├── README.md                    # 项目主页
├── AI_SETUP.md                  # AI 配置指南
├── TESTING.md                   # 测试报告
├── V2_PLAN.md                   # 开发计划
├── V2.0_RELEASE_NOTES.md        # v2.0 发布说明
│
├── docs/                        # 文档中心 ⭐
│   ├── README.md                # 本文档（导航）
│   ├── GDB_INTEGRATION_GUIDE.md # 使用指南
│   └── GDB_INTEGRATION_DESIGN.md# 技术设计
│
├── backend/                     # 后端代码
│   ├── analyzers/              # 分析器模块
│   ├── parsers/                # 解析器模块
│   ├── gdb/                    # GDB 集成模块
│   └── app.py                  # Flask 主程序
│
└── frontend/                    # 前端代码
    ├── index.html              # 主页面
    ├── app.js                  # 主逻辑
    ├── gdb_client.js           # GDB 客户端
    └── style.css               # 样式表
```

---

## 🔍 常见问题快速链接

### 安装和配置

- **如何安装？** → [README - 快速开始](../README.md#-快速开始)
- **如何启用 AI？** → [AI_SETUP.md](../AI_SETUP.md)
- **支持哪些架构？** → [README - 系统要求](../README.md)

### 实时 GDB 功能

- **如何连接 GDB？** → [GDB_INTEGRATION_GUIDE.md - 快速开始](GDB_INTEGRATION_GUIDE.md#-快速开始)
- **连接失败怎么办？** → [GDB_INTEGRATION_GUIDE.md - 常见问题](GDB_INTEGRATION_GUIDE.md#-注意事项)
- **如何调试 xv6？** → [GDB_INTEGRATION_GUIDE.md - 场景 1](GDB_INTEGRATION_GUIDE.md#场景-1-调试-xv6-内核崩溃)

### 技术和开发

- **系统架构是什么？** → [GDB_INTEGRATION_DESIGN.md - 架构](GDB_INTEGRATION_DESIGN.md#-系统架构)
- **如何扩展功能？** → [GDB_INTEGRATION_DESIGN.md - API 文档](GDB_INTEGRATION_DESIGN.md#-核心模块-api)
- **测试如何运行？** → [TESTING.md](../TESTING.md)

---

## 📚 推荐学习路径

### 入门路径（1 小时）

```
1. 阅读主 README 了解项目
   ↓
2. 按照快速开始安装运行
   ↓
3. 尝试静态分析功能
   ↓
4. 阅读 GDB 使用指南
   ↓
5. 尝试实时 GDB 功能
```

### 深入路径（3-5 小时）

```
1. 完成入门路径
   ↓
2. 阅读技术设计文档
   ↓
3. 查看源代码结构
   ↓
4. 运行测试脚本
   ↓
5. 尝试调试真实项目（xv6/Pintos）
```

### 贡献者路径（全面）

```
1. 完成深入路径
   ↓
2. 研究测试报告和 Bug 修复
   ↓
3. 查看开发计划
   ↓
4. Fork 仓库并设置开发环境
   ↓
5. 选择一个功能开始贡献
```

---

## 🆘 获取帮助

遇到问题？这里有几种方式获取帮助：

1. **查看文档** - 大部分问题都能在文档中找到答案
2. **查看示例** - 文档中有大量实际使用示例
3. **提交 Issue** - [GitHub Issues](https://github.com/yourusername/os_debug/issues)
4. **联系作者** - 通过邮件或 GitHub

---

## 📝 文档贡献

文档也需要你的贡献！

### 如何贡献文档

1. **发现错误** - 提交 Issue 或直接 PR
2. **添加示例** - 分享你的使用场景
3. **改进说明** - 让文档更清晰易懂
4. **翻译文档** - 帮助更多人使用

### 文档风格指南

- 使用清晰的标题层级
- 提供代码示例
- 添加截图或图表（如果有帮助）
- 保持简洁但完整
- 使用表格组织信息

---

## 🔄 文档版本

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v2.0 | 2025-11-17 | 新增 GDB 集成文档、发布说明 |
| v1.0 | 之前 | 初始文档、AI 配置、测试报告 |

---

## 📮 反馈

文档有问题？有改进建议？

- 📧 发送邮件
- 💬 提交 Issue
- 🔧 直接提 PR

我们随时欢迎你的反馈！

---

**最后更新**: 2025-11-17 | **版本**: v2.0
