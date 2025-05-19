import os
import random
import time
import logging
import sys

import html2text
from markdownify import markdownify

from flomo.flomo_api import FlomoApi
from notionify import notion_utils
from notionify.md2notion import Md2NotionUploader
from notionify.notion_cover_list import cover
from notionify.notion_helper import NotionHelper
from utils import truncate_string, is_within_n_days


# 禁用所有第三方库的日志
logging.getLogger('notion_client').setLevel(logging.ERROR)  # 提高到 ERROR 级别
logging.getLogger('notion_client.api_endpoints').setLevel(logging.ERROR)  # 提高到 ERROR 级别
logging.getLogger('urllib3').setLevel(logging.ERROR)  # 禁用 urllib3 日志
logging.getLogger('requests').setLevel(logging.ERROR)  # 禁用 requests 日志
logging.getLogger('httpx').setLevel(logging.ERROR)  # 禁用 httpx 日志

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('flomo2notion')

def split_long_text(text, max_length=1900):
    """
    将长文本分割成多个小块，每个块不超过指定的最大长度
    
    Args:
        text (str): 要分割的文本
        max_length (int): 每个块的最大长度，默认为1900（留出一些余量）
        
    Returns:
        list: 分割后的文本块列表
    """
    if not text or len(text) <= max_length:
        return [text]
        
    chunks = []
    current_pos = 0
    text_length = len(text)
    
    while current_pos < text_length:
        # 如果剩余文本长度小于等于最大长度，直接添加
        if current_pos + max_length >= text_length:
            chunks.append(text[current_pos:])
            break
            
        # 尝试在最大长度位置附近找到一个合适的分割点（如句号、换行符等）
        end_pos = current_pos + max_length
        
        # 优先在句号、问号、感叹号、换行符处分割
        for char in ['\n', '。', '！', '？', '.', '!', '?']:
            last_char_pos = text.rfind(char, current_pos, end_pos)
            if last_char_pos != -1 and last_char_pos > current_pos:
                end_pos = last_char_pos + 1
                break
                
        # 如果没找到合适的分割点，就在最大长度处直接分割
        chunks.append(text[current_pos:end_pos])
        current_pos = end_pos
        
    return chunks

def clean_backticks(text):
    """彻底清理字符串中的所有反引号和多余空格"""
    if not text:
        return ""
    # 移除所有反引号和规范化空格
    return text.replace('`', '').strip()

def mask_sensitive_info(text, mask_length=4):
    """
    对敏感信息进行脱敏处理
    
    Args:
        text (str): 需要脱敏的文本
        mask_length (int): 保留的字符数量
        
    Returns:
        str: 脱敏后的文本
    """
    if not text or len(text) <= mask_length:
        return text
        
    # 保留前几个字符，其余用*代替
    return text[:mask_length] + '*' * (len(text) - mask_length)

class Flomo2Notion:
    def __init__(self):
        self.flomo_api = FlomoApi()
        self.notion_helper = NotionHelper()
        self.uploader = Md2NotionUploader()
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0

    def insert_memo(self, memo):
        # 检查记录是否已删除
        if memo.get('deleted_at') is not None:
            self.skip_count += 1
            return
        
        # 处理 None 内容
        image_blocks = []
        if memo['content'] is None:
            # 如果有文件，将它们作为内容
            if memo.get('files') and len(memo['files']) > 0:
                content_md = "# 图片备忘录\n\n"
                for i, file in enumerate(memo['files']):
                    if file.get('url'):
                        try:
                            # 使用新函数彻底清理 URL 和名称
                            clean_url = clean_backticks(file['url'])
                            clean_name = clean_backticks(file.get('name', '图片'))
                            
                            # 添加图片块
                            image_blocks.append({
                                "type": "image",
                                "image": {
                                    "type": "external",
                                    "external": {
                                        "url": clean_url
                                    }
                                }
                            })
                            
                            # 同时保留在 Markdown 中
                            content_md += f"![{clean_name}]({clean_url})\n\n"
                        except Exception as e:
                            logger.error(f"❌ 图片处理失败: {str(e)}")
            else:
                content_md = ""  # 如果没有文件则为空内容
            content_text = content_md
        else:
            content_md = markdownify(memo['content'])
            content_text = html2text.html2text(memo['content'])
        
        parent = {"database_id": self.notion_helper.page_id, "type": "database_id"}
        properties = {
            "标题": notion_utils.get_title(
                truncate_string(content_text)
            ),
            "标签": notion_utils.get_multi_select(
                memo['tags']
            ),
            "是否置顶": notion_utils.get_select("否" if memo['pin'] == 0 else "是"),
            # 文件的处理方式待定
            # "文件": notion_utils.get_file(""),
            # slug是文章唯一标识
            "slug": notion_utils.get_rich_text(memo['slug']),
            "创建时间": notion_utils.get_date(memo['created_at']),
            "更新时间": notion_utils.get_date(memo['updated_at']),
            "来源": notion_utils.get_select(memo['source']),
            "链接数量": notion_utils.get_number(memo['linked_count']),
        }
    
        random_cover = random.choice(cover)
    
        try:
            page = self.notion_helper.client.pages.create(
                parent=parent,
                icon=notion_utils.get_icon("https://www.notion.so/icons/target_red.svg"),
                cover=notion_utils.get_icon(random_cover),
                properties=properties,
            )
            
            # 检查内容长度，如果超过限制则分割
            if len(content_md) > 2000:
                content_chunks = split_long_text(content_md)
                
                # 逐块上传
                for i, chunk in enumerate(content_chunks):
                    self.uploader.uploadSingleFileContent(self.notion_helper.client, chunk, page['id'])
            else:
                self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])
                
            # 在上传完内容后添加图片块
            if image_blocks and len(image_blocks) > 0:
                try:
                    self.notion_helper.client.blocks.children.append(
                        block_id=page['id'],
                        children=image_blocks
                    )
                except Exception as e:
                    logger.error(f"❌ 添加图片块失败: {str(e)}")
            
            self.success_count += 1
        except Exception as e:
            logger.error(f"❌ 记录插入失败: {str(e)}")
            self.error_count += 1
            raise

    def update_memo(self, memo, page_id):
        # 检查记录是否已删除
        if memo.get('deleted_at') is not None:
            try:
                # 将 Notion 页面归档（相当于删除）
                self.notion_helper.client.pages.update(
                    page_id=page_id,
                    archived=True
                )
                self.success_count += 1
                logger.info(f"✅ 归档记录成功: {memo['slug']}")
                return
            except Exception as e:
                logger.error(f"❌ 归档记录失败: {str(e)}")
                self.error_count += 1
                raise
        
        # 处理 None 内容
        image_blocks = []
        if memo['content'] is None:
            # 如果有文件，将它们作为内容
            if memo.get('files') and len(memo['files']) > 0:
                content_md = "# 图片备忘录\n\n"
                
                # 创建图片块列表
                for i, file in enumerate(memo['files']):
                    if file.get('url'):
                        try:
                            # 使用新函数彻底清理 URL 和名称
                            clean_url = clean_backticks(file['url'])
                            clean_name = clean_backticks(file.get('name', '图片'))
                            
                            # 添加图片块
                            image_blocks.append({
                                "type": "image",
                                "image": {
                                    "type": "external",
                                    "external": {
                                        "url": clean_url
                                    }
                                }
                            })
                            
                            # 同时保留在 Markdown 中，以防块创建失败
                            content_md += f"![{clean_name}]({clean_url})\n\n"
                        except Exception as e:
                            logger.error(f"❌ 图片处理失败: {str(e)}")
            else:
                content_md = ""  # 如果没有文件则为空内容
            content_text = content_md
        else:
            content_md = markdownify(memo['content'])
            content_text = html2text.html2text(memo['content'])
        
        # 只更新内容
        properties = {
            "标题": notion_utils.get_title(
                truncate_string(content_text)
            ),
            "更新时间": notion_utils.get_date(memo['updated_at']),
            "链接数量": notion_utils.get_number(memo['linked_count']),
            "标签": notion_utils.get_multi_select(
                memo['tags']
            ),
            "是否置顶": notion_utils.get_select("否" if memo['pin'] == 0 else "是"),
        }
        
        try:
            page = self.notion_helper.client.pages.update(page_id=page_id, properties=properties)
        
            # 先清空page的内容，再重新写入
            self.notion_helper.clear_page_content(page["id"])
        
            # 检查内容长度，如果超过限制则分割
            if len(content_md) > 2000:
                content_chunks = split_long_text(content_md)
                
                # 逐块上传
                for i, chunk in enumerate(content_chunks):
                    self.uploader.uploadSingleFileContent(self.notion_helper.client, chunk, page['id'])
            else:
                self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])
                
            # 在上传完内容后添加图片块
            if image_blocks and len(image_blocks) > 0:
                try:
                    self.notion_helper.client.blocks.children.append(
                        block_id=page['id'],
                        children=image_blocks
                    )
                except Exception as e:
                    logger.error(f"❌ 添加图片块失败: {str(e)}")
                
            self.success_count += 1
        except Exception as e:
            logger.error(f"❌ 记录更新失败: {str(e)}")
            self.error_count += 1
            raise

    # 具体步骤：
    # 1. 调用flomo web端的api从flomo获取数据
    # 2. 轮询flomo的列表数据，调用notion api将数据同步写入到database中的page
    def sync_to_notion(self):
        logger.info("🚀 开始同步 Flomo 到 Notion")
        start_time = time.time()
        
        # 1. 调用flomo web端的api从flomo获取数据
        authorization = os.getenv("FLOMO_TOKEN")
        if not authorization:
            logger.error("❌ 未设置 FLOMO_TOKEN 环境变量")
            return
            
        memo_list = []
        latest_updated_at = "0"

        logger.info("📥 获取 Flomo 数据...")
        while True:
            try:
                new_memo_list = self.flomo_api.get_memo_list(authorization, latest_updated_at)
                if not new_memo_list:
                    break
                memo_list.extend(new_memo_list)
                latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))
                logger.info(f"📥 已获取 {len(memo_list)} 条记录")
            except Exception as e:
                logger.error(f"❌ 获取 Flomo 数据失败: {str(e)}")
                return
        
        # 不要过滤掉已删除的记录，而是记录它们
        deleted_memo_slugs = set()
        for memo in memo_list:
            if memo.get('deleted_at') is not None:
                deleted_memo_slugs.add(memo['slug'])
        
        logger.info(f"📥 共有 {len(memo_list)} 条记录，其中 {len(deleted_memo_slugs)} 条已删除")
        
        # 2. 调用notion api获取数据库存在的记录，用slug标识唯一，如果存在则更新，不存在则写入
        logger.info("🔍 查询 Notion 数据库...")
        try:
            notion_memo_list = self.notion_helper.query_all(self.notion_helper.page_id)
            slug_map = {}
            for notion_memo in notion_memo_list:
                slug_map[notion_utils.get_rich_text_from_result(notion_memo, "slug")] = notion_memo.get("id")
            # logger.info(f"🔍 Notion 数据库中已有 {len(slug_map)} 条记录")
        except Exception as e:
            logger.error(f"❌ 查询 Notion 数据库失败: {str(e)}")
            return

        # 3. 轮询flomo的列表数据
        total = len(memo_list)
        logger.info(f"🔄 开始处理 {total} 条 Flomo 记录")
        
        for i, memo in enumerate(memo_list):
            progress = f"[{i+1}/{total}]"
            # logger.info(f"{progress} 🔍 处理记录 - {memo['slug']}")
            # 3.1 判断memo的slug是否存在，不存在则写入
            # 3.2 防止大批量更新，只更新更新时间为制定时间的数据（默认为1天）
            if memo['slug'] in slug_map.keys():
                # 是否全量更新，默认否
                full_update = os.getenv("FULL_UPDATE", False)
                interval_day = os.getenv("UPDATE_INTERVAL_DAY", 1)
                if not full_update and not is_within_n_days(memo['updated_at'], interval_day):
                    logger.info(f"{progress} ⏭️ 跳过记录 - 更新时间超过 {interval_day} 天")
                    self.skip_count += 1
                    continue

                try:
                    page_id = slug_map[memo['slug']]
                    logger.info(f"{progress} 🔄 更新记录")
                    self.update_memo(memo, page_id)
                    logger.info(f"{progress} ✅ 更新成功")
                except Exception as e:
                    logger.error(f"{progress} ❌ 更新失败: {str(e)}")
            else:
                try:
                    logger.info(f"{progress} 📝 新记录")
                    self.insert_memo(memo)
                    logger.info(f"{progress} ✅ 插入成功")
                except Exception as e:
                    logger.error(f"{progress} ❌ 插入失败: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("📊 同步统计:")
        logger.info(f"  - 总记录数: {total}")
        logger.info(f"  - 成功处理: {self.success_count}")
        logger.info(f"  - 跳过记录: {self.skip_count}")
        logger.info(f"  - 失败记录: {self.error_count}")
        logger.info(f"  - 耗时: {duration:.2f} 秒")
        logger.info("✅ 同步完成")


if __name__ == "__main__":
    # flomo同步到notion入口
    flomo2notion = Flomo2Notion()
    flomo2notion.sync_to_notion()

    # notionify key
    # secret_IHWKSLUTqUh3A8TIKkeXWePu3PucwHiRwDEcqNp5uT3
