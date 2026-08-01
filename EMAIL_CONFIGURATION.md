# GitHub Actions 邮件配置说明

本项目支持通过 GitHub Actions 自动发送邮件通知，包括成功生成通知、空数据通知和错误通知。

## 配置步骤

### 1. 在 GitHub 仓库中设置 Secrets

需要在 GitHub 仓库的 `Settings > Secrets and variables > Actions` 中添加以下环境变量：

| 变量名称 | 说明 | 示例值 |
|---------|------|--------|
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 服务器端口 | `587` |
| `SMTP_USER` | 发件人邮箱地址 | `your-email@gmail.com` |
| `SMTP_PASSWORD` | 邮箱密码或授权码 | `your-app-password` |
| `NOTIFICATION_TO` | 收件人邮箱地址 | `recipient@example.com` |
| `DISABLE_EMAIL_NOTIFICATION` | 是否禁用邮件通知 | `false` (默认) |
| `GITHUB_PAGES_URL` | GitHub Pages 访问 URL | `https://yourusername.github.io/ai-daily-skill` |

### 2. 常见邮件服务提供商配置示例

#### Gmail 配置

- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: 你的 Gmail 邮箱地址
- `SMTP_PASSWORD`: 应用密码（需要开启两步验证并创建应用密码）

**注意**：
1. Gmail 默认禁用了不安全的应用访问，需要在 Gmail 设置中开启
2. 推荐使用应用密码而非原始密码
3. 应用密码获取步骤：
   - 登录 Gmail
   - 进入 `管理你的 Google 账户`
   - 选择 `安全性`
   - 开启 `两步验证`
   - 在 `应用密码` 部分生成新的应用密码

#### QQ 邮箱配置

- `SMTP_HOST`: `smtp.qq.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: 你的 QQ 邮箱地址
- `SMTP_PASSWORD`: 授权码（需要在 QQ 邮箱中开启 SMTP 服务并获取）

**注意**：
1. 授权码获取步骤：
   - 登录 QQ 邮箱
   - 进入 `设置 > 账户`
   - 在 `POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务` 部分开启 `SMTP服务`
   - 点击 `生成授权码` 按照提示操作

#### 163 邮箱配置

- `SMTP_HOST`: `smtp.163.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: 你的 163 邮箱地址
- `SMTP_PASSWORD`: 授权码（需要在 163 邮箱中开启 SMTP 服务并获取）

**注意**：
1. 授权码获取步骤：
   - 登录 163 邮箱
   - 进入 `设置 > POP3/SMTP/IMAP`
   - 开启 `SMTP服务`
   - 设置授权码

### 3. 测试邮件发送

配置完成后，可以通过以下方式测试邮件发送功能：

1. **手动触发 GitHub Actions 工作流**：
   - 进入 GitHub 仓库的 `Actions` 页面
   - 选择 `AI Daily News Generator` 工作流
   - 点击 `Run workflow` 按钮手动触发
   - 查看工作流日志，确认邮件是否发送成功

2. **本地测试**：
   - 复制 `.env.example` 文件为 `.env`
   - 填写邮件相关配置
   - 运行 `python src/test_email.py` 测试邮件发送

### 4. 邮件通知类型

系统支持三种邮件通知类型：

1. **成功通知**：当 AI Daily 生成成功时发送，包含完整的资讯内容
2. **空数据通知**：当目标日期没有找到资讯内容时发送
3. **错误通知**：当生成过程中发生错误时发送，包含错误信息和 GitHub Actions 日志链接

## 常见问题与 Troubleshooting

### 1. 邮件发送失败

**问题**：GitHub Actions 日志显示 `SMTPAuthenticationError`

**解决方案**：
- 检查 `SMTP_PASSWORD` 是否正确（注意使用授权码而非原始密码）
- 确认邮件服务提供商是否开启了 SMTP 服务
- 检查是否需要开启 "允许不安全的应用访问" 或类似设置

### 2. 邮件发送超时

**问题**：GitHub Actions 日志显示 `SMTPConnectError` 或超时错误

**解决方案**：
- 检查 `SMTP_HOST` 和 `SMTP_PORT` 是否正确
- 确认网络连接是否正常
- 尝试使用不同的 SMTP 端口（如 465 或 25）

### 3. 邮件内容显示异常

**问题**：收到的邮件内容格式异常或不完整

**解决方案**：
- 确认 HTML 生成是否正常
- 检查 `GITHUB_PAGES_URL` 是否正确配置
- 尝试调整邮件模板中的 CSS 样式

### 4. 禁用邮件通知

如果不需要邮件通知，可以设置 `DISABLE_EMAIL_NOTIFICATION` 为 `true` 来禁用。

## 邮件模板说明

邮件模板包含以下部分：

1. **头部**：显示生成状态、日期和资讯条数
2. **AI Daily 内容**：包含完整的生成结果
3. **页脚**：显示生成时间和自动化标识

邮件使用响应式设计，支持在不同设备上正常显示。

## 代码结构

邮件相关代码位于以下文件：

- `src/notifier.py`: 邮件通知核心代码
- `src/config.py`: 邮件配置参数定义
- `.github/workflows/daily.yml`: GitHub Actions 工作流配置

## 更多信息

- 查看 `src/notifier.py` 了解邮件发送的详细实现
- 查看 GitHub Actions 日志了解邮件发送的执行情况
- 参考邮件服务提供商的文档获取更详细的配置信息
