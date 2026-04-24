# DBTalk - 文本提交与管理系统

DBTalk 是一个基于 Python Tkinter 和 MongoDB Atlas 的桌面端文本提交与管理应用。它采用 **MVC (Model-View-Controller/Service)** 分层架构，支持用户注册登录、文本提交、管理员审核、公告发布、公开交流广场以及个人账号管理等功能。

## 📁 项目结构

```
DBTalk/
├── models/               # 数据模型（预留）
│   └── user.py
├── utils/                # 工具模块
│   ├── config_manager.py # 配置加密与加载
│   └── db.py             # 数据库连接与操作（单例模式）
├── views/                # GUI 界面
│   ├── login_window.py   # 登录/注册窗口
│   ├── user_window.py    # 普通用户主界面
│   ├── admin_window.py   # 管理员主界面
│   └── settings_window.py# 云端配置窗口
├── .env                  # 环境变量（MongoDB连接串等）
├── .gitignore
├── config.py             # 配置类
├── main.py               # 程序入口
├── requirements.txt      # 依赖列表
├── test_connection.py    # 数据库连接测试脚本
└── playground-1.mongodb.js # MongoDB Playground（可选）
```

---

## ✨ 已实现功能

### 用户端
- **注册**：新用户填写用户名、密码、邮箱，密码经 SHA256 哈希后存入 MongoDB。
- **登录**：验证用户名与密码，区分普通用户与管理员。
- **文本提交**：用户可输入标题和内容，提交后状态为“pending”，存入 `submissions` 集合。
- **提交历史**：以表格形式查看自己所有提交（时间、标题、状态）。
- **个人信息**：查看用户名、邮箱、注册时间。

### 管理员端
- **所有提交**：查看所有用户的提交记录，支持双击查看详情，并可“批准”或“拒绝”提交，更新状态。
- **用户管理**：查看所有用户列表（用户名、邮箱、角色、注册时间、状态）。
- **统计信息**：展示总用户数、总提交数、待审核数等卡片。

### 系统特性
- **云端数据库**：通过 MongoDB Atlas 存储数据，支持首次使用时图形化配置连接字符串，并加密保存。
- **自动创建管理员**：若数据库中无管理员，首次启动时自动创建默认管理员 `admin/admin123`。
- **连接状态提示**：窗口底部显示当前数据库连接状态。
- **菜单栏**：文件菜单可打开云端配置；帮助菜单显示关于信息。

---
```
链接：
mongodb+srv://<your_username>:<your_password>@cluster0.xxxxx.mongodb.net/

dpp
dpp5258
{
  "username": "dpp",
  "password": "3eef3b66a0bd4a39666241de7c23467bd4ddb22cb83320fb59a72c66b3315ab3",
  "email": "dpp@example.com",
  "role": "admin",
  "created_at": { "$date": "2026-03-11T00:00:00.000Z" },
  "is_active": true
}
3eef3b66a0bd4a39666241de7c23467bd4ddb22cb83320fb59a72c66b3315ab3
```

## 🚀 快速开始

### 1. 环境准备
- Python 3.10+
- MongoDB Atlas 账号及集群（免费版即可）

### 2. 克隆项目并安装依赖
```bash
git clone <仓库地址>
cd DBTalk
pip install -r requirements.txt
```

### 3. 配置数据库连接
- 复制 `.env.example` 为 `.env`（若没有则新建），填写您的 MongoDB Atlas 连接串：
  ```env
  MONGODB_URI=mongodb+srv://用户名:密码@集群地址/?retryWrites=true&w=majority
  DATABASE_NAME=DBTalk1
  ```
- 或直接运行程序，在菜单 `文件` → `云端配置` 中输入连接串并测试保存。

### 4. 运行程序
```bash
python main.py
```

### 5. 登录测试
- 默认管理员：`admin` / `admin123`（首次启动自动创建）。
- 或注册新用户，并在数据库中将其 `role` 改为 `admin` 以获取管理员权限。

---

## 🔧 主要依赖
- `pymongo`：MongoDB 驱动
- `python-dotenv`：环境变量管理
- `cryptography`：连接字符串加密
- `tkinter`：Python 标准 GUI 库（无需额外安装）

---

## 📌 注意事项
- 确保 MongoDB Atlas 网络访问权限已配置（建议添加 `0.0.0.0/0` 或您的公网 IP）。
- 密码使用 SHA256 哈希存储，不可逆。
- 若修改集合名称，请同步修改 `utils/db.py` 中的对应集合名。

---

## 🤝 贡献
欢迎提交 Issue 或 Pull Request 来扩展功能（如邮件通知、附件上传、搜索筛选等）。

---

## 📄 许可证
[MIT](LICENSE)

---

**Happy Coding!**