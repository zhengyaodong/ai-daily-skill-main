#!/usr/bin/env python3
"""
AI Daily 主入口
自动获取 AI 资讯并生成精美的 HTML 页面
"""
import sys
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import (
    ZHIPU_API_KEY,
    DAILY_NEWS_LOOKBACK_DAYS,
    OUTPUT_DIR,
    ENABLE_IMAGE_GENERATION,
    REPORT_TIMEZONE,
)
from src.rss_fetcher import RSSFetcher
from src.claude_analyzer import ClaudeAnalyzer
from src.html_generator import HTMLGenerator
from src.notifier import EmailNotifier
from src.image_generator import ImageGenerator
from src.xiaohongshu_generator import XiaohongshuGenerator


def print_banner():
    """打印程序横幅"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║                                                              ║
║   AI Daily - AI 资讯日报自动生成器                          ║
║                                                              ║
║   多源 RSS 聚合 · 百炼大模型分析                          ║
║   精美 HTML 页面 · 自动部署                                 ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)


def get_target_date(days_offset: int = 1) -> str:
    """
    获取目标日期

    Args:
        days_offset: 向前偏移的天数，默认1天（昨天）

    Returns:
        格式化的日期字符串 (YYYY-MM-DD)
    """
    target_date = datetime.now(REPORT_TIMEZONE).date() - timedelta(days=days_offset)
    return target_date.isoformat()


def main():
    """主函数"""
    print_banner()

    # 检查环境变量
    if not ZHIPU_API_KEY:
        print("❌ 错误: K2_API_KEY 环境变量未设置")
        print("   请设置阿里百炼的 API Key")
        sys.exit(1)

    # 初始化组件
    notifier = EmailNotifier()
    email_enabled = notifier._is_configured()
    image_enabled = ENABLE_IMAGE_GENERATION
    total_steps = 6 if email_enabled else 5
    if image_enabled:
        total_steps += 1

    try:
        # 1. 计算目标日期 (今天 - 1天，即昨天)
        target_date = get_target_date(days_offset=1)
        print(f"[目标日期] {target_date}")
        print(f"   (北京时间: {datetime.now(REPORT_TIMEZONE):%Y-%m-%d %H:%M:%S %z})")
        print()

        # 2. 下载并解析 RSS
        print(f"[步骤 1/{total_steps}] 下载 RSS...")
        fetcher = RSSFetcher()
        rss_data = fetcher.fetch()

        # 显示 RSS 信息
        date_range = fetcher.get_date_range(rss_data)
        if date_range[0] and date_range[1]:
            print(f"   RSS 日期范围: {date_range[0]} ~ {date_range[1]}")
        print()

        # 3. 查找目标日期的内容
        print(f"[步骤 2/{total_steps}] 筛选日报候选资讯...")
        content = fetcher.get_digest_content(target_date, rss_data)

        if not content:
            reason = f"RSS 中未找到截至 {target_date} 的近 {DAILY_NEWS_LOOKBACK_DAYS} 日资讯。"
            print(f"   {reason}")
            if email_enabled:
                notifier.send_empty(
                    target_date,
                    f"{reason}"
                    f"RSS 可用日期范围: {date_range[0]} ~ {date_range[1]}"
                )

            # 生成空页面
            generator = HTMLGenerator()
            generator.generate_css()
            generator.generate_empty(target_date, reason)
            generator.update_index(target_date, {"summary": ["暂无资讯"]})

            print("   完成")
            return

        print(f"   找到资讯: {content.get('title', '')[:60]}...")
        counts = Counter(article["published_date"] for article in content["articles"])
        distribution = "，".join(f"{day} {count} 条" for day, count in counts.items())
        print(f"   候选日期分布: {distribution}")
        print()

        # 4. 分析失败时由下方错误处理退出，避免发布不完整的日报。
        print(f"[步骤 3/{total_steps}] 调用百炼大模型进行资讯分析...")
        analyzer = ClaudeAnalyzer()
        result = analyzer.analyze(content, target_date)

        # 检查分析状态
        if result.get("status") == "empty":
            print("   分析结果为空")
            if email_enabled:
                notifier.send_empty(target_date, result.get("reason", "内容分析为空"))
            return

        print()

        # 5. 生成 HTML
        print(f"[步骤 4/{total_steps}] 生成 HTML 页面...")
        generator = HTMLGenerator()
        generator.generate_css()

        # 生成日报页面
        html_path = generator.generate_daily(result)
        print(f"   文件路径: {html_path}")
        print()

        # 计算总资讯数
        total_items = sum(
            len(cat.get('items', []))
            for cat in result.get('categories', [])
        )

        # 6. 生成分享图片（可选）
        image_path = None
        xhs_path = None
        if image_enabled:
            print(f"[步骤 5/{total_steps}] 生成分享卡片图片...")
            image_gen = ImageGenerator()
            image_path = image_gen.generate_from_analysis_result(
                result,
                output_path=str(Path(OUTPUT_DIR) / "images" / f"{target_date}.png")
            )
            if image_path:
                print(f"   图片已保存: {image_path}")
            else:
                print("   图片生成失败或跳过")

            # 生成小红书封面
            print(f"   生成小红书封面...")
            xhs_gen = XiaohongshuGenerator()
            xhs_path = xhs_gen.generate(result)
            print(f"   小红书封面: {xhs_path}")
            print()
        else:
            print("   (图片生成未启用，跳过)")
            print()

        # 7. 发送成功通知（可选）
        if email_enabled:
            step_num = 6 if image_enabled else 5
            print(f"[步骤 {step_num}/{total_steps}] 发送邮件通知...")
            notifier.send_success(target_date, total_items)
            print()
        else:
            print("   (邮件通知未配置，跳过)")
            print()

        # 完成
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║   ✅ 任务完成!                                              ║")
        print("║                                                              ║")
        print(f"║   日期: {target_date}                                        ║")
        print(f"║   资讯数: {total_items} 条                                          ║")
        print(f"║   主题: {result.get('theme', 'blue')}                                                ║")
        print("║                                                              ║")
        print("╚════════════════════════════════════════════════════════════╝")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(130)

    except Exception as e:
        print(f"\n[错误] 执行过程出错: {e}")
        import traceback
        traceback.print_exc()

        # 发送错误通知（如果配置了邮件）
        if email_enabled:
            try:
                target_date = get_target_date(days_offset=1)
                notifier.send_error(target_date, str(e))
            except:
                pass

        sys.exit(1)


if __name__ == "__main__":
    main()
