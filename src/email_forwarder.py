#!/usr/bin/env python3
"""
邮件自动转发程序
每隔1小时检查学校邮箱，并将新邮件转发到QQ邮箱
"""
import imaplib
import smtplib
import email
import os
import json
import time
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.message import MIMEMessage
from typing import List, Set, Optional
from pathlib import Path

from src.config import (
    IMAP_HOST,
    IMAP_PORT,
    IMAP_USER,
    IMAP_PASSWORD,
    FORWARD_SMTP_HOST,
    FORWARD_SMTP_PORT,
    FORWARD_SMTP_USER,
    FORWARD_SMTP_PASSWORD,
    FORWARD_TO_EMAIL,
    STATE_FILE_PATH
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_forwarder.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailForwarder:
    """邮件转发器"""
    
    def __init__(self):
        """初始化邮件转发器"""
        self.imap_host = IMAP_HOST
        self.imap_port = IMAP_PORT
        self.imap_user = IMAP_USER
        self.imap_password = IMAP_PASSWORD
        
        self.smtp_host = FORWARD_SMTP_HOST
        self.smtp_port = FORWARD_SMTP_PORT
        self.smtp_user = FORWARD_SMTP_USER
        self.smtp_password = FORWARD_SMTP_PASSWORD
        self.forward_to = FORWARD_TO_EMAIL
        
        self.state_file = Path(STATE_FILE_PATH)
        self.processed_emails: Set[str] = self._load_processed_emails()
        
    def _load_processed_emails(self) -> Set[str]:
        """加载已处理邮件ID列表"""
        if not self.state_file.exists():
            return set()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_emails', []))
        except Exception as e:
            logger.warning(f"加载已处理邮件列表失败: {e}")
            return set()
    
    def _save_processed_emails(self):
        """保存已处理邮件ID列表"""
        try:
            data = {
                'processed_emails': list(self.processed_emails),
                'last_update': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存已处理邮件列表失败: {e}")
    
    def _get_email_message(self, mail: imaplib.IMAP4_SSL, uid: str) -> Optional[email.message.Message]:
        """获取邮件消息对象"""
        try:
            result, data = mail.uid('fetch', uid, '(RFC822)')
            if result != 'OK' or not data[0]:
                return None
            
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            return email_message
        except Exception as e:
            logger.error(f"获取邮件失败 (UID: {uid}): {e}")
            return None
    
    def _forward_email(self, msg: email.message.Message) -> bool:
        """转发邮件"""
        try:
            # 创建新邮件
            forward_msg = MIMEMultipart()
            
            # 设置邮件头
            forward_msg['From'] = self.smtp_user
            forward_msg['To'] = self.forward_to
            forward_msg['Subject'] = f"Fwd: {msg.get('Subject', '(无主题)')}"
            
            # 添加原始邮件信息
            original_from = msg.get('From', '未知发件人')
            original_date = msg.get('Date', '未知日期')
            original_subject = msg.get('Subject', '(无主题)')
            
            # 构建邮件正文
            text_body = f"""
-------- 原始邮件 --------
发件人: {original_from}
日期: {original_date}
主题: {original_subject}

"""
            
            # 提取原始邮件正文
            body = self._extract_body(msg)
            if body:
                text_body += body
            
            # 将原始邮件作为附件
            forward_msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            
            # 附加原始邮件
            forward_msg.attach(MIMEMessage(msg))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
                if self.smtp_port == 587:
                    smtp.starttls()
                smtp.login(self.smtp_user, self.smtp_password)
                smtp.send_message(forward_msg)
            
            logger.info(f"邮件转发成功: {original_subject}")
            return True
            
        except Exception as e:
            logger.error(f"转发邮件失败: {e}")
            return False
    
    def _extract_body(self, msg: email.message.Message) -> str:
        """提取邮件正文"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # 跳过附件
                if "attachment" in content_disposition:
                    continue
                
                # 获取文本内容
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body += payload.decode(charset, errors='ignore')
                    except Exception as e:
                        logger.warning(f"解析文本内容失败: {e}")
                
                elif content_type == "text/html":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            html_body = payload.decode(charset, errors='ignore')
                            # 简单的HTML转纯文本（可选）
                            body += html_body
                    except Exception as e:
                        logger.warning(f"解析HTML内容失败: {e}")
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
            except Exception as e:
                logger.warning(f"解析邮件正文失败: {e}")
        
        return body
    
    def check_and_forward(self) -> int:
        """
        检查并转发新邮件
        
        Returns:
            转发的邮件数量
        """
        forwarded_count = 0
        
        try:
            # 连接IMAP服务器
            logger.info(f"连接IMAP服务器: {self.imap_host}:{self.imap_port}")
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            
            # 登录
            logger.info(f"登录邮箱: {self.imap_user}")
            mail.login(self.imap_user, self.imap_password)
            
            # 选择收件箱
            mail.select('INBOX')
            
            # 搜索未读邮件（或所有邮件，根据需求调整）
            # 这里搜索所有邮件，因为我们要根据已处理列表来判断
            result, data = mail.uid('search', None, 'ALL')
            
            if result != 'OK':
                logger.error("搜索邮件失败")
                mail.logout()
                return 0
            
            email_ids = data[0].split()
            logger.info(f"找到 {len(email_ids)} 封邮件")
            
            # 处理每封邮件
            for email_id in email_ids:
                uid = email_id.decode('utf-8')
                
                # 跳过已处理的邮件
                if uid in self.processed_emails:
                    continue
                
                # 获取邮件
                msg = self._get_email_message(mail, uid)
                if not msg:
                    continue
                
                # 转发邮件
                if self._forward_email(msg):
                    self.processed_emails.add(uid)
                    forwarded_count += 1
                    # 每转发一封邮件就保存一次，避免中断导致重复转发
                    self._save_processed_emails()
            
            # 断开连接
            mail.logout()
            
            logger.info(f"本次共转发 {forwarded_count} 封邮件")
            return forwarded_count
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP错误: {e}")
            return forwarded_count
        except Exception as e:
            logger.error(f"检查邮件时发生错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return forwarded_count


def run_once():
    """运行一次检查和转发"""
    logger.info("=" * 60)
    logger.info("开始检查邮件...")
    logger.info("=" * 60)
    
    forwarder = EmailForwarder()
    count = forwarder.check_and_forward()
    
    logger.info("=" * 60)
    logger.info(f"完成！共转发 {count} 封邮件")
    logger.info("=" * 60)
    
    return count


def run_loop(interval_hours: float = 1.0):
    """循环运行邮件检查和转发"""
    logger.info("=" * 60)
    logger.info("邮件自动转发服务启动")
    logger.info(f"检查间隔: {interval_hours} 小时")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 60)
    
    interval_seconds = interval_hours * 3600
    
    try:
        while True:
            run_once()
            logger.info(f"等待 {interval_hours} 小时后再次检查...")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("\n收到停止信号，正在退出...")
    except Exception as e:
        logger.error(f"运行过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 只运行一次
        run_once()
    else:
        # 循环运行，默认1小时
        interval = 1.0
        if len(sys.argv) > 1:
            try:
                interval = float(sys.argv[1])
            except ValueError:
                logger.warning(f"无效的间隔时间: {sys.argv[1]}，使用默认值 1.0 小时")
        
        run_loop(interval)
