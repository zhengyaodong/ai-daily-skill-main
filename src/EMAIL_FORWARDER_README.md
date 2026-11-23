# 邮件自动转发程序使用说明

## 功能说明

这个程序可以自动从学校邮箱（zyd@mail.gzus.edu.cn）读取邮件，并将所有新邮件转发到QQ邮箱（283406@qq.com）。

## 主要特性

- ✅ 使用 IMAP 协议读取学校邮箱邮件
- ✅ 使用 SMTP 协议转发邮件到目标邮箱
- ✅ 自动记录已转发邮件，避免重复转发
- ✅ 支持定时运行（默认每小时检查一次）
- ✅ 完整的日志记录功能
- ✅ 错误处理和重试机制

## 配置说明

### 1. 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 学校邮箱IMAP配置（接收邮件）
IMAP_HOST=imap.mail.gzus.edu.cn
IMAP_PORT=993
IMAP_USER=zyd@mail.gzus.edu.cn
IMAP_PASSWORD=你的学校邮箱密码或授权码

# 转发SMTP配置（发送邮件，使用QQ邮箱）
FORWARD_SMTP_HOST=smtp.qq.com
FORWARD_SMTP_PORT=587
FORWARD_SMTP_USER=你的QQ邮箱账号@qq.com
FORWARD_SMTP_PASSWORD=你的QQ邮箱授权码（不是密码！）

# 转发目标邮箱
FORWARD_TO_EMAIL=283406@qq.com

# 状态文件路径（可选，默认为 email_forwarder_state.json）
# STATE_FILE_PATH=email_forwarder_state.json
```

### 2. 获取QQ邮箱授权码

QQ邮箱需要使用授权码而不是登录密码：

1. 登录 QQ邮箱网页版
2. 点击"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 点击"生成授权码"，按照提示获取授权码
6. 将授权码填入 `FORWARD_SMTP_PASSWORD`

### 3. 学校邮箱配置

确保学校邮箱已开启IMAP服务：
- 登录学校邮箱网页版
- 查看邮箱设置中的"POP3/IMAP/SMTP服务"选项
- 确保IMAP服务已开启

## 使用方法

### 方法1：单次运行（测试用）

```bash
python email_forwarder.py --once
```

只运行一次检查和转发，适合测试配置是否正确。

### 方法2：定时运行（推荐）

```bash
# 默认每小时检查一次
python email_forwarder.py

# 或者指定检查间隔（小时）
python email_forwarder.py 2  # 每2小时检查一次
```

程序会持续运行，每隔指定时间自动检查一次邮件。

### 方法3：后台运行（Windows）

创建批处理文件 `run_email_forwarder.bat`：

```batch
@echo off
cd /d %~dp0
python email_forwarder.py
pause
```

或者使用 `nssm` 将其安装为 Windows 服务。

### 方法4：后台运行（Linux/Mac）

使用 `nohup` 或 `systemd` 服务：

```bash
# 使用 nohup
nohup python email_forwarder.py > email_forwarder.log 2>&1 &

# 或者使用 screen
screen -S email_forwarder
python email_forwarder.py
# 按 Ctrl+A 然后 D 退出 screen
```

## 日志说明

程序运行时会生成 `email_forwarder.log` 日志文件，记录：
- 每次检查的详细信息
- 转发的邮件数量和主题
- 错误信息和异常堆栈

## 状态文件

程序会在当前目录生成 `email_forwarder_state.json` 文件（可配置），记录：
- 已处理的邮件ID列表
- 最后更新时间

如果删除此文件，程序会重新处理所有邮件（可能导致重复转发）。

## 注意事项

1. **授权码不是密码**：QQ邮箱必须使用授权码，不能使用登录密码
2. **网络连接**：确保服务器能够访问IMAP和SMTP服务器
3. **防火墙**：确保防火墙允许访问邮箱服务器端口
4. **邮箱容量**：定期清理邮箱，避免邮箱容量不足
5. **首次运行**：首次运行时会转发邮箱中的所有邮件，之后只转发新邮件

## 故障排查

### 问题1：连接IMAP服务器失败

**可能原因：**
- IMAP服务器地址或端口错误
- 网络连接问题
- 防火墙阻止连接

**解决方法：**
- 检查 `IMAP_HOST` 和 `IMAP_PORT` 配置
- 确认网络连接正常
- 检查防火墙设置

### 问题2：认证失败

**可能原因：**
- 用户名或密码错误
- 需要使用授权码而不是密码
- 邮箱服务未开启IMAP

**解决方法：**
- 确认用户名和密码正确
- 使用授权码替代密码
- 在邮箱设置中开启IMAP服务

### 问题3：转发邮件失败

**可能原因：**
- SMTP服务器配置错误
- 授权码错误
- 网络问题

**解决方法：**
- 检查SMTP配置
- 确认使用的是授权码
- 检查网络连接

### 问题4：重复转发邮件

**可能原因：**
- 状态文件被删除
- 程序异常退出导致状态未保存

**解决方法：**
- 保留状态文件 `email_forwarder_state.json`
- 检查日志文件查看错误信息

## 技术说明

- **IMAP协议**：用于读取邮件，支持查看邮件而不删除
- **SMTP协议**：用于发送邮件
- **邮件状态管理**：使用JSON文件记录已处理邮件的UID
- **错误处理**：完善的异常捕获和日志记录
- **邮件格式**：保留原始邮件格式，作为附件转发

## 更新日志

- v1.0.0 (2026-01-20)
  - 初始版本
  - 支持IMAP读取和SMTP转发
  - 支持定时运行和状态管理
