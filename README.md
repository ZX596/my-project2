# 用户认证系统

基于Flask的用户认证管理系统，支持学生、教师、管理员三种角色的用户注册、登录、权限控制和批量导入功能。

## 功能特性

### 用户管理
- 三种角色: 学生（13位学号）、教师（8位工号）、管理员（8位工号）
- 注册验证: 学号/工号格式验证、唯一性检查
- 密码安全: 使用bcrypt加密存储密码
- 登录功能: 支持学号/工号登录、

### 文件管理
- 文件上传功能：支持上传png,pdf,jpg,jpeg类型的文件
- 文件查看功能：点击查看图标即可查看上传的文件


### 批量导入
- Excel导入: 支持.xlsx/.xls格式文件批量导入用户
- 格式验证: 自动验证数据格式和完整性
- 重复检查: 自动检测并处理重复记录
- 详细报告: 生成包含成功、失败、重复记录的导入报告
- 操作日志: 记录所有导入操作的历史记录

### 权限控制（RBAC）
- 角色权限: 预定义三种角色的权限集合
- 权限验证: 基于角色的访问控制
- 功能隔离: 不同角色只能访问授权功能

## 系统要求

- Python 3.8+
- MySQL 5.7+
- Web浏览器如Edge、Google


## 安装部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd user-auth-system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

- 创建数据库
```sql
CREATE DATABASE user_auth_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- 导入初始数据
```bash
# 导入用户表结构
mysql -u root -p user_auth_system < schema.sql

# 导入初始管理员
mysql -u root -p user_auth_system -e "INSERT INTO users (username, password, role) VALUES ('admin', '{hashed_password}', 'admin');"
```

### 3. 运行应用

```bash
# 设置环境变量
export FLASK_APP=app
export FLASK_ENV=development

# 初始化数据库
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# 运行应用
flask run
```

## 批量导入流程

1. 管理员登录后进入“批量导入”页面。
2. 下载模板，按要求填写用户信息（支持学生、教师、管理员）。
3. 上传Excel文件，系统自动校验格式、唯一性，批量创建用户。
4. 导入完成后，系统生成详细导入报告，展示每条记录的导入状态和原因。
5. 所有导入操作均记录在导入日志，可随时查询历史记录。

## 导入报告说明

- 导入报告包含每条记录的行号、用户名、姓名、角色、状态（成功/失败/重复）、失败原因等。
- 支持导出报告，便于后续核查和修正。

## 数据库结构简述

- users：用户表，包含id、username、password、name、email、role、创建/更新时间等字段。
- permissions：权限表，定义系统权限点。
- role_permissions**：角色与权限关联表（RBAC）。
- import_logs：导入日志表，记录每次批量导入的详细信息和报告数据。