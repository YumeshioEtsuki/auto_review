# AutoReview - 智能题库练习系统

一个支持多种题型的智能复习系统，自动解析题目文档并提供交互式答题体验。

## ✨ 功能特点

- 📄 **多格式支持**：解析 TXT 和 DOCX 文档
- 🎯 **六种题型**：
  - 选择题 / 多选题（智能区分）
  - 填空题 / 判断题 / 简答题 / 计算题
- 🤖 **智能对齐**：自动匹配含答案和纯题干文档
- ✅ **实时判题**：即时反馈答题正误
- 📒 **错题本**：自动记录错题，支持查看和清空
- 🎨 **友好界面**：基于 Streamlit 的现代化 Web UI
- 📝 **格式识别**：支持 DOCX 文档中的
  - **加粗**：标记重点题目
  - **删除线**：自动过滤跳过的题目
  - **下划线**：标记关键要点

## 📝 DOCX 文档格式说明

### 格式标记识别

| 格式 | 含义 | 说明 |
|------|------|------|
| **加粗** | 重点题 | 题干或选项加粗时，UI会特殊显示 |
| ~~删除线~~ | 跳过此题 | 标记为删除线的题目会被自动过滤 |
| <u>下划线</u> | 关键点 | 标记要点或重要选项 |

### 示例文档

```
1. 以下哪个是 Python 的特点？（此行加粗）
A. 编译型语言
B. 解释型语言（此行下划线表示要点）
C. 汇编语言
D. 机器语言

2. ~~已删除的题目~~（此行删除线，会被跳过）
...

3. 多选题：以下正确的有（有多个正确答案）
A. 选项1
B. 选项2
C. 选项3
D. 选项4

答案：B、D（多个正确答案）
```

## 🚀 快速开始

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/YumeshioEtsuki/auto_review.git
cd auto_review

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

## 📚 使用说明

### 1. 准备题目文件
将题目文档放入 `data/raw/` 目录：
- **含答案文档**：包含题目和答案
- **纯题干文档**：只包含题目

支持格式：`.txt`、`.docx`

### 2. 题目格式示例

```
1. 选择题示例：
A. 选项A
B. 选项B
C. 选项C

2. 填空题：Python 的创始人是_______。

3. 判断题：Python 是开源语言。（）

4. 多选题（答案中有多个字母）：
A. 正确1
B. 正确2
C. 错误
D. 错误2

答案：A、B
```

### 3. 答案文档格式

```
1. B
2. Guido van Rossum
3. 正确
4. A、B
```

## 🛠️ 技术栈

- **Python 3.12+**
- **Streamlit** - Web 界面
- **python-docx** - DOCX 解析与格式识别
- **Pydantic** - 数据验证

## 📂 项目结构

```
auto_review/
├── data/                  # 数据目录
│   ├── raw/              # 原始题目文档
│   └── processed/        # 处理后的JSON
├── models/               # 数据模型
├── parsers/              # 文件解析器
│   ├── text_parser.py    # TXT解析
│   └── docx_parser.py    # DOCX解析（含格式识别）
├── recognizers/          # 题目识别和答案对齐
│   ├── question_detector.py  # 题型检测（支持多选题）
│   └── answer_aligner.py     # 答案对齐
├── ui/                   # Streamlit 界面
│   └── streamlit_app.py
├── config.py             # 配置和正则表达式
├── main.py               # 入口文件
└── requirements.txt      # 依赖列表
```

## 🌐 部署到 Streamlit Cloud

1. 将代码上传到 GitHub
2. 访问 https://share.streamlit.io
3. 连接 GitHub 仓库
4. 设置入口文件为 `ui/streamlit_app.py`
5. 点击 Deploy

## 📊 更新日志

### v1.1.0 - 格式识别和多选题支持（2026-01-08）
- ✅ 支持 DOCX 文档格式识别（加粗/删除线/下划线）
- ✅ 自动过滤标记为删除线的题目
- ✅ 改进选择题和多选题区分算法
- ✅ 保留格式标记用于 UI 显示
- ✅ Enter 键快速提交答案
- ✅ 错题本功能完善

### v1.0.0 - 初始版本（2026-01-06）
- ✅ 基础题目解析和答案对齐
- ✅ 支持 TXT/DOCX 文档
- ✅ Streamlit Web 界面
- ✅ 错题本功能

## 📝 许可证

MIT License
