"""
邮件通知模块
发送任务执行结果的邮件通知
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from src.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    NOTIFICATION_TO,
    GITHUB_PAGES_URL,
    DISABLE_EMAIL_NOTIFICATION,
    OUTPUT_DIR
)


class EmailNotifier:
    """邮件通知器"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        to_email: str = None
    ):
        """
        初始化邮件通知器

        Args:
            host: SMTP 服务器地址
            port: SMTP 端口
            user: 发件邮箱
            password: 邮箱密码/授权码
            to_email: 收件邮箱
        """
        self.host = host or SMTP_HOST
        self.port = port or SMTP_PORT
        self.user = user or SMTP_USER
        self.password = password or SMTP_PASSWORD
        self.to_email = to_email or NOTIFICATION_TO

        # GitHub Actions 环境变量（用于生成日志链接）
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_run_id = os.getenv("GITHUB_RUN_ID")
        self.github_server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")

    def _get_actions_url(self) -> Optional[str]:
        """获取 GitHub Actions 运行日志链接"""
        if self.github_repository and self.github_run_id:
            return f"{self.github_server_url}/{self.github_repository}/actions/runs/{self.github_run_id}"
        return None

    def _get_page_url(self, date: str) -> str:
        """获取生成的页面 URL"""
        base_url = GITHUB_PAGES_URL or os.getenv("GITHUB_PAGES_URL", "")
        if base_url:
            return f"{base_url.rstrip('/')}/{date}.html"
        return f"{date}.html"

    def send_success(self, date: str, summary_count: int) -> bool:
        """
        发送成功通知

        Args:
            date: 日期
            summary_count: 资讯条数

        Returns:
            是否发送成功
        """
        page_url = self._get_page_url(date)
        subject = f"✅ AI Daily 生成成功 - {date}"
        
        # 读取生成的HTML文件内容
        html_file_path = os.path.join(OUTPUT_DIR, f"{date}.html")
        ai_daily_content = ""
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                ai_daily_content = f.read()
                
            # 简化HTML，移除不支持的CSS和复杂样式
            # 1. 移除外部CSS链接
            ai_daily_content = ai_daily_content.replace('<link rel="stylesheet" href="css/styles.css">', '')
            
            # 2. 添加内联基本样式
            basic_styles = """
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { text-align: center; margin-bottom: 40px; }
                .logo-icon { font-size: 32px; margin-bottom: 10px; }
                h1 { font-size: 24px; color: #333; margin: 0; }
                .date-badge { display: inline-block; padding: 8px 16px; background: #E3F2FD; color: #1565C0; border-radius: 20px; font-size: 14px; margin-top: 10px; }
                
                .summary-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 30px; }
                .section-title { font-size: 18px; color: #333; margin: 0 0 15px 0; }
                .summary-list { list-style: none; padding: 0; margin: 0; }
                .summary-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; color: #666; }
                .summary-item:last-child { border-bottom: none; }
                
                .category-section { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 30px; }
                .category-header { display: flex; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #E3F2FD; padding-bottom: 10px; }
                .category-icon { font-size: 20px; margin-right: 10px; }
                .category-title { font-size: 18px; color: #333; margin: 0; flex: 1; }
                .category-count { background: #E3F2FD; color: #1565C0; padding: 4px 10px; border-radius: 12px; font-size: 14px; }
                
                .news-grid { display: flex; flex-direction: column; gap: 15px; }
                .news-card { border: 1px solid #f0f0f0; padding: 15px; border-radius: 8px; }
                .news-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
                .news-title { font-size: 16px; color: #333; margin: 0; flex: 1; }
                .item-link { background: #42A5F5; color: white; padding: 4px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; white-space: nowrap; }
                .news-summary { font-size: 14px; color: #666; margin: 0 0 10px 0; line-height: 1.5; }
                .item-tags { display: flex; flex-wrap: wrap; gap: 5px; }
                .tag { background: #f0f0f0; color: #666; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
                
                .keywords-footer { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); font-size: 12px; color: #999; }
                
                /* 隐藏动画和复杂效果 */
                .background-glow, .geometric-lines { display: none; }
            </style>
            """
            ai_daily_content = ai_daily_content.replace('</head>', f'{basic_styles}</head>')
            
            # 3. 简化容器样式
            ai_daily_content = ai_daily_content.replace('class="container"', 'class="container" style="max-width: 800px; margin: 0 auto; padding: 20px;"')
            
        except Exception as e:
            print(f"⚠️ 读取HTML文件失败: {e}")
            # 如果读取失败，回退到原来的简单邮件
            ai_daily_content = f"""
            <p>AI Daily 已生成，但无法在邮件中显示详细内容。</p>
            <p>您可以点击下方链接查看完整内容：</p>
            <a href="{page_url}" style="display: block; padding: 14px 24px; background: #42A5F5; color: white; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 500;">查看 AI Daily 页面</a>
            """
        
        # 构建完整邮件内容
        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #42A5F5, #1A3A52); padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 20px;">
            <span style="font-size: 48px;">✅</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">AI Daily 生成成功</h1>
            <div style="color: white; opacity: 0.9; margin-top: 10px;">日期: {date} | 资讯条数: {summary_count} 条</div>
        </div>
        
        <!-- AI Daily 内容 -->
        <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            {ai_daily_content}
        </div>
        
        <!-- 页脚 -->
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>此邮件由 AI Daily 自动生成</p>
            <p>时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def send_empty(self, date: str, reason: str = "RSS中未找到对应日期的资讯") -> bool:
        """
        发送空数据通知

        Args:
            date: 日期
            reason: 原因

        Returns:
            是否发送成功
        """
        subject = f"📭 AI Daily 无数据 - {date}"
        actions_url = self._get_actions_url()

        actions_button = ""
        if actions_url:
            actions_button = f'<a href="{actions_url}" style="display: inline-block; padding: 10px 20px; background: #FFA726; color: white; text-decoration: none; border-radius: 6px;">查看 Actions 日志</a>'

        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
    <div style="max-width: 600px; margin: 40px auto; padding: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08);">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #FFA726, #3D2415); padding: 30px; text-align: center;">
            <span style="font-size: 48px;">📭</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">今日暂无资讯</h1>
        </div>

        <!-- 内容 -->
        <div style="padding: 30px;">
            <div style="background: #FFF3E0; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 5px 0; color: #E65100;"><strong>📅 目标日期:</strong> {date}</p>
                <p style="margin: 5px 0; color: #E65100;"><strong>📝 原因:</strong> {reason}</p>
            </div>

            <div style="text-align: center;">
                {actions_button}
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

            <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                此邮件由 GitHub Actions 自动发送
            </p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def send_error(self, date: str, error: str) -> bool:
        """
        发送错误通知（带 GitHub Actions 日志链接）

        Args:
            date: 日期
            error: 错误信息

        Returns:
            是否发送成功
        """
        subject = f"❌ AI Daily 生成失败 - {date}"
        actions_url = self._get_actions_url()

        actions_section = ""
        if actions_url:
            actions_section = f'''
                <div style="text-align: center; margin-top: 24px;">
                    <a href="{actions_url}" style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #F06292, #E91E63); color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">🔍 查看 GitHub Actions 日志</a>
                </div>
            '''

        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #fafafa;">
    <div style="max-width: 600px; margin: 40px auto; padding: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08);">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #F06292, #C62828); padding: 30px; text-align: center;">
            <span style="font-size: 48px;">❌</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">生成过程出错</h1>
        </div>

        <!-- 内容 -->
        <div style="padding: 30px;">
            <div style="background: #FFEBEE; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 5px 0; color: #C62828;"><strong>📅 目标日期:</strong> {date}</p>
                <p style="margin: 5px 0; color: #C62828;"><strong>⏰ 时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>

            <p style="color: #555; margin-bottom: 12px;"><strong>错误信息:</strong></p>
            <pre style="background: #263238; color: #ECEFF1; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; margin-bottom: 20px;">{self._escape_html(error)}</pre>

            {actions_section}

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

            <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                请检查 GitHub Actions 日志获取详细信息
            </p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def _is_configured(self) -> bool:
        """检查邮件是否已配置"""
        # 如果明确禁用了邮件功能，则返回False
        if DISABLE_EMAIL_NOTIFICATION:
            return False
        # 否则检查必要的配置项
        return all([self.host, self.user, self.password, self.to_email])

    def _send(self, subject: str, html_body: str) -> bool:
        """
        发送邮件的底层方法

        Args:
            subject: 邮件主题
            html_body: HTML 邮件正文

        Returns:
            是否发送成功
        """
        # 检查配置，未配置则静默跳过
        if not self._is_configured():
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = self.to_email

            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            print(f"📧 尝试连接邮件服务器: {self.host}:{self.port}")
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                print("📧 连接成功，开始加密通信...")
                server.starttls()
                print("📧 加密通信已建立，尝试登录...")
                server.login(self.user, self.password)
                print("📧 登录成功，发送邮件...")
                server.send_message(msg)

            print(f"✅ 邮件已发送: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ 邮件发送失败: 认证错误 - 检查用户名和密码是否正确，或Gmail安全设置")
            print(f"   错误详情: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"❌ 邮件发送失败: 无法连接到邮件服务器 - 检查网络连接和防火墙设置")
            print(f"   错误详情: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            print(f"❌ 邮件发送失败: 服务器连接断开")
            print(f"   错误详情: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ 邮件发送失败: SMTP协议错误")
            print(f"   错误详情: {e}")
            return False
        except Exception as e:
            print(f"❌ 邮件发送失败: 其他错误")
            print(f"   错误详情: {e}")
            return False

    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))


def send_success_email(date: str, summary_count: int) -> bool:
    """便捷函数：发送成功通知"""
    notifier = EmailNotifier()
    return notifier.send_success(date, summary_count)


def send_empty_email(date: str, reason: str = "") -> bool:
    """便捷函数：发送空数据通知"""
    notifier = EmailNotifier()
    return notifier.send_empty(date, reason)


def send_error_email(date: str, error: str) -> bool:
    """便捷函数：发送错误通知"""
    notifier = EmailNotifier()
    return notifier.send_error(date, error)
