# AutoReview - 智能题库练习系统

一个支持多种题型的智能复习系统，自动解析题目文档并提供交互式答题体验。

## ✨ 功能特点

- 📄 **多格式支持**：解析 TXT 和 DOCX 文档
- 🎯 **六种题型**：选择题、多选题、填空题、判断题、简答题、计算题
- 🤖 **智能对齐**：自动匹配含答案和纯题干文档
- ✅ **实时判题**：即时反馈答题正误
- 📒 **错题本**：自动记录错题，支持查看和清空
- 🎨 **友好界面**：基于 Streamlit 的现代化 Web UI

## 🚀 快速开始

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/auto_review.git
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
1. 以下哪个是 Python 的特点？
A. 编译型语言
B. 解释型语言
C. 汇编语言
D. 机器语言

2. 填空题：Python 的创始人是_______。

3. 判断题：Python 是开源语言。（）
```

### 3. 答案文档格式

```
1. B
2. Guido van Rossum
3. 正确
```

## 🛠️ 技术栈

- **Python 3.12+**
- **Streamlit** - Web 界面
- **python-docx** - DOCX 解析
- **Pydantic** - 数据验证

## 📂 项目结构

```
auto_review/
├── data/                  # 数据目录
│   ├── raw/              # 原始题目文档
│   └── processed/        # 处理后的JSON
├── models/               # 数据模型
├── parsers/              # 文件解析器
├── recognizers/          # 题目识别和答案对齐
├── ui/                   # Streamlit 界面
│   └── streamlit_app.py
├── main.py               # 入口文件
└── requirements.txt      # 依赖列表
```

## 🌐 部署到 Streamlit Cloud

1. 将代码上传到 GitHub
2. 访问 https://share.streamlit.io
3. 连接 GitHub 仓库
4. 设置入口文件为 `ui/streamlit_app.py`
5. 点击 Deploy

## 📝 许可证

MIT License
