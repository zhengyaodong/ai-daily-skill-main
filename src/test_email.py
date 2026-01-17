#!/usr/bin/env python3
"""
Gmail SMTP 连接测试脚本
用于诊断和测试 Gmail SMTP 服务器连接和邮件发送功能
"""

import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_gmail_smtp():
    """测试 Gmail SMTP 连接和邮件发送"""
    print("=" * 50)
    print("Gmail SMTP 连接测试脚本")
    print("=" * 50)
    print()
    
    # 从环境变量获取配置
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    to_email = os.getenv("NOTIFICATION_TO") or smtp_user
    
    # 检查必要的配置
    if not smtp_user or not smtp_password:
        print("❌ 错误: 缺少必要的环境变量")
        print("   请确保已设置 SMTP_USER 和 SMTP_PASSWORD")
        return False
    
    print("📋 测试配置:")
    print(f"   SMTP 服务器: {smtp_host}:{smtp_port}")
    print(f"   发件人: {smtp_user}")
    print(f"   收件人: {to_email}")
    print()
    print("🔍 网络环境检测:")
    print("   如果您使用的是公司/学校网络，可能会限制对外部邮件服务器的访问")
    print()
    
    # 创建测试邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Gmail SMTP 测试邮件'
    msg['From'] = smtp_user
    msg['To'] = to_email
    
    # 邮件内容
    text_content = "这是一封测试邮件，用于测试 Gmail SMTP 连接功能。"
    html_content = """
    <html>
        <body>
            <h2>Gmail SMTP 测试邮件</h2>
            <p>这是一封测试邮件，用于测试 Gmail SMTP 连接功能。</p>
            <p>如果您收到这封邮件，说明 SMTP 配置正确且邮件发送功能正常。</p>
        </body>
    </html>
    """
    
    # 附加邮件内容
    msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        print("📧 尝试连接 Gmail SMTP 服务器...")
        # 连接服务器
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            print("✅ 连接成功!")
            
            # 启用 TLS 加密
            print("📧 启用 TLS 加密...")
            server.starttls()
            print("✅ TLS 加密已启用!")
            
            # 登录验证
            print("📧 尝试登录 Gmail 账号...")
            server.login(smtp_user, smtp_password)
            print("✅ 登录成功!")
            
            # 发送邮件
            print("📧 发送测试邮件...")
            server.send_message(msg)
            print("✅ 邮件发送成功!")
            print()
            print("🎉 测试完成! 您应该会收到一封来自自己的测试邮件。")
            
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ 认证错误!")
        print("   可能的原因:")
        print("   1. 用户名或密码不正确")
        print("   2. Gmail 账号未启用 '不太安全的应用访问'")
        print("   3. 未使用应用专用密码（适用于启用了两步验证的账号）")
        print("   解决方案:")
        print("   - 检查用户名和密码是否正确")
        print("   - 对于两步验证账号，请使用应用专用密码")
        print("   - 开启 '不太安全的应用访问'（如果使用普通密码）")
        return False
        
    except smtplib.SMTPConnectError:
        print("❌ 连接错误!")
        print("   可能的原因:")
        print("   1. 网络连接问题")
        print("   2. 防火墙或杀毒软件阻止连接")
        print("   3. SMTP 服务器地址或端口错误")
        print("   解决方案:")
        print("   - 检查网络连接")
        print("   - 暂时关闭防火墙或杀毒软件测试")
        print("   - 确认 SMTP 服务器和端口设置正确")
        return False
        
    except (socket.timeout, TimeoutError):
        print("❌ 连接超时!")
        print("   可能的原因:")
        print("   1. 网络延迟过高或网络受限")
        print("   2. Gmail 服务器暂时不可用")
        print("   3. 防火墙或网络设置阻止了连接")
        print("   解决方案:")
        print("   - 稍后重试")
        print("   - 检查网络连接")
        print("   - 尝试使用其他邮件服务商，如 Outlook、QQ 邮箱等")
        return False
        
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        print("   请检查错误信息并尝试解决问题")
        return False

if __name__ == "__main__":
    test_gmail_smtp()