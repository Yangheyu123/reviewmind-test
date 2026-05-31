# reviewmind-test

ReviewMind AI 审查测试仓库 — 用于演示 ReviewMind 的 PR Review 能力。

## 项目结构

```
├── auth.py              # 认证服务（JWT、密码哈希、登录限流）
├── user_handler.py      # 用户管理 API（增删查改、CSV 导出）
├── config.py            # 应用配置管理
├── utils/
│   └── helpers.py       # 工具函数（输入清洗、格式化）
├── tests/
│   └── test_auth.py     # 自动化测试
├── requirements.txt     # 依赖声明
└── README.md
```

## 快速开始

```bash
pip install -r requirements.txt
python -c "from auth import AuthService; s=AuthService(); print(s.generate_token(1))"
```
