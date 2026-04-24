# DBTalk 项目重构思路记录

## 🎯 重构目标
将原有的“视图与逻辑混杂”的架构，重构为清晰的 **MVC (Model-View-Controller/Service)** 分层架构。
核心原则：**小步快跑，分步实施，确保每一步完成后程序均可正常运行。**

---

## 📂 最终期望架构
DBTalk/
├── models/               # 数据模型层：定义常量、数据结构、实体类
│   ├── __init__.py
│   ├── constants.py      # 全局常量（如角色、状态枚举）
│   ├── user.py           # 用户模型（含权限常量）
│   └── submission.py     # 提交模型（含状态常量、文档构建方法）
├── services/             # 业务逻辑层：核心业务规则、数据处理、权限控制
│   ├── __init__.py
│   ├── auth_service.py   # 认证服务（登录、注册、密码哈希）
│   ├── user_service.py   # 用户管理服务（增删改查、角色变更、权限校验）
│   └── submission_service.py # 提交服务（审核、发布、查询、公告管理）
├── views/                # 视图层：纯 UI 实现，只负责展示和事件绑定
│   ├── __init__.py
│   ├── login_window.py
│   ├── user_window.py
│   ├── admin_window.py
│   └── settings_window.py
├── utils/                # 工具层：基础设施（数据库连接、配置管理）
│   ├── __init__.py
│   ├── db.py             # 数据库驱动包装（单例，仅保留原子操作）
│   └── config_manager.py # 配置加密加载
├── main.py               # 入口
├── config.py             # 全局配置
└── ...

---

## 🚀 分步实施计划

### 第一步：建立“模型与常量中心” (Models)
**目标**：消除代码中的魔法字符串（如 "pending", "admin", "dpp"），统一数据定义和结构构建。
**操作**：
1. **新建 `models/constants.py`**：
   - 定义 `UserRole` (ADMIN='admin', USER='user')。
   - 定义 `SubmissionStatus` (PENDING='pending', APPROVED='approved', REJECTED='rejected')。
   - 定义 `INITIAL_ADMIN_USERNAME` ('dpp')。
2. **完善 `models/submission.py`**：
   - 实现 `SubmissionModel` 类，提供 `create_document()` 静态方法，用于标准化构建提交文档（包含默认字段如 `is_announcement=False`）。
3. **完善 `models/user.py`**：
   - 引入常量，替换硬编码的用户名判断。
4. **全局替换**：
   - 在 `utils/db.py`、`views/admin_window.py`、`views/user_window.py` 中引入这些常量。
   - 替换所有硬编码字符串（如 `"pending"` -> `SubmissionStatus.PENDING`）。
**验证**：运行程序，确保登录、提交、审核功能正常，无字符串拼写错误导致的 Bug。

### 第二步：剥离“提交与公告业务” (Services - Submission)
**目标**：将管理员界面中复杂的“审核、刷新列表、发布公告”逻辑移入服务层。
**操作**：
1. **新建 `services/submission_service.py`**：
   - 注入 `Database` 实例。
   - 实现 `get_all_submissions()`：获取所有提交（供管理员）。
   - 实现 `get_approved_public_submissions()`：获取交流广场数据（供普通用户）。
   - 实现 `approve_submission(id)` / `reject_submission(id)`：更新状态。
   - 实现 `create_announcement(admin_user, title, content)`：封装公告发布逻辑（设置 `is_announcement=True`, `status=approved`）。
2. **修改 `views/admin_window.py`**：
   - 实例化 `SubmissionService`。
   - `refresh_submissions()` 调用服务层获取数据。
   - `post_announcement()` 调用 `submission_service.create_announcement()`。
   - 审核按钮点击事件调用服务层方法。
   - **关键点**：视图层不再直接构造 MongoDB 文档，也不直接调用 `db.submissions.insert_one`。
3. **修改 `views/user_window.py`**：
   - 交流广场刷新逻辑改为调用 `SubmissionService.get_approved_public_submissions()`（可选，若第一步未完全剥离，可在此步统一）。
**验证**：登录管理员，测试刷新列表、批准/拒绝提交、发布公告，确保功能与重构前一致，且公告能正确显示在交流广场（或按需求隐藏）。

### 第三步：剥离“用户与认证业务” (Services - Auth & User)
**目标**：将登录/注册逻辑和用户管理逻辑移入服务层，封装权限判断。
**操作**：
1. **新建 `services/auth_service.py`**：
   - 迁移 `utils/db.py` 中的 `hash_password` 方法到服务层或工具类。
   - 实现 `login(username, password)`：返回用户字典或 None。
   - 实现 `register(username, password, email)`：调用 DB 插入，处理重复用户名异常。
2. **新建 `services/user_service.py`**：
   - 实现 `get_all_users()`：返回脱敏后的用户列表。
   - 实现 `update_role(operator, target_username, new_role)`：
     - **核心逻辑迁移**：将 `admin_window.py` 中复杂的权限判断（如“初始管理员不可被降级”、“非初始管理员不可管理其他管理员”）移入此处。
     - 抛出异常或返回错误信息如果权限不足。
   - 实现 `delete_user(operator, target_username)`：同样包含权限校验。
3. **修改 `views/login_window.py`**：
   - 调用 `AuthService` 进行登录/注册。
4. **修改 `views/admin_window.py`**：
   - 用户管理标签页调用 `UserService` 进行列表刷新、角色变更、删除操作。
   - 移除视图层中的权限判断 `if/else` 块，仅处理服务层返回的结果（成功/失败消息）。
**验证**：测试新用户注册、老用户登录、管理员升级/删除普通用户、尝试违规操作（如普通管理员删除初始管理员），确保权限逻辑正确且视图层代码大幅简化。

### 第四步：清理、规范与文档更新
**目标**：统一架构风格，彻底解耦 View 与 DB，更新文档。
**操作**：
1. **清理 `views/user_window.py`**：
   - 确保“提交文本”功能也通过 `SubmissionService`（或专门的 `UserSubmissionService`）进行，而不是直接调用 `db.create_submission`。
   - 确保“个人信息”获取通过 `UserService.get_user_info`。
2. **精简 `utils/db.py`**：
   - 移除所有包含业务逻辑的方法（如 `authenticate_user`, `create_submission`, `get_stats` 等复杂查询）。
   - 仅保留原子操作：`connect`, `insert_one`, `find_one`, `find_many`, `update_one`, `delete_one`。
   - 确保 `Database` 类纯粹作为 DAO (Data Access Object) 存在。
3. **更新 `README.md`**：
   - 更新项目结构图，反映新的 `services/` 和 `models/` 目录。
   - 简要说明各层职责及调用链：View -> Service -> Model/Utils -> DB。
4. **代码审查**：
   - 检查所有 View 文件，确保没有 `from utils.db import Database` 后直接进行业务逻辑操作的情况（除了必要的初始化）。
**验证**：全流程测试（注册->登录->提交->审核->管理->交流广场），确认所有功能正常，代码结构清晰，View 层代码行数显著减少且更易读。

---

## 💡 重构核心原则
1. **视图层 (Views)**：只负责“画界面”、“获取用户输入”和“展示结果”。**禁止**包含业务判断、数据组装或直接数据库操作。
2. **服务层 (Services)**：包含所有“怎么做”的逻辑。负责事务控制、权限校验、数据组装、调用 DAO 层。
3. **模型层 (Models)**：定义“是什么”。包含常量、枚举、数据结构类、验证规则。
4. **工具层 (Utils)**：提供“用什么做”。数据库连接单例、加密工具、配置加载。

通过这四步，项目将从“脚本式”代码进化为“工程化”架构，极大提升可维护性和扩展性。