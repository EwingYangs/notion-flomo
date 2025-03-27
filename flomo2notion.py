import os
import time
import re

import html2text
from markdownify import markdownify

from flomo.flomo_api import FlomoApi
from notionify import notion_utils
from notionify.md2notion import Md2NotionUploader
from notionify.notion_helper import NotionHelper
from utils import truncate_string, is_within_n_days

# 标签对应的emoji映射，可以根据需要扩展
TAG_EMOJI_MAP = {
    "得到": "📚",
    "创业想法": "💡",
    # 添加更多标签和对应的emoji
}

# 默认emoji，当没有匹配的标签时使用
DEFAULT_EMOJI = "📌"

class Flomo2Notion:
    def __init__(self):
        self.flomo_api = FlomoApi()
        self.notion_helper = NotionHelper()
        self.uploader = Md2NotionUploader()

    def get_emoji_for_tags(self, tags):
        """根据标签获取对应的emoji图标"""
        if not tags or len(tags) == 0:
            return DEFAULT_EMOJI
        
        # 尝试使用第一个标签匹配emoji
        first_tag = tags[0]
        # 检查是否有精确匹配
        for tag, emoji in TAG_EMOJI_MAP.items():
            if tag in first_tag:
                return emoji
        
        # 如果没有匹配到，返回默认emoji
        return DEFAULT_EMOJI

    def process_content(self, html_content):
        """预处理HTML内容，移除或替换可能导致Markdown解析问题的元素"""
        # 替换 [XX][YY] 格式的文本，这种格式容易被误认为是Markdown链接或脚注
        processed = re.sub(r'\[([^\]]+)\]\[([^\]]+)\]', r'【\1】【\2】', html_content)
        # 替换其他可能导致问题的模式
        processed = re.sub(r'\[([^\]]+)\]', r'【\1】', processed)
        return processed

    def insert_memo(self, memo):
        print("insert_memo:", memo)

        # 预处理内容，处理可能导致问题的格式
        processed_content = self.process_content(memo['content'])
        content_md = markdownify(processed_content)
        parent = {"database_id": self.notion_helper.page_id, "type": "database_id"}
        content_text = html2text.html2text(processed_content)
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

        # 获取标签对应的emoji
        emoji = self.get_emoji_for_tags(memo['tags'])

        page = self.notion_helper.client.pages.create(
            parent=parent,
            icon={"type": "emoji", "emoji": emoji},
            properties=properties,
        )

        # 在page里面添加content
        try:
            self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])
        except Exception as e:
            print(f"Error uploading content: {e}")
            # 发生错误时，尝试使用纯文本块
            from html.parser import HTMLParser
            
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.strict = False
                    self.convert_charrefs= True
                    self.text = []
                def handle_data(self, d):
                    self.text.append(d)
                def get_data(self):
                    return ''.join(self.text)
                    
            def strip_tags(html):
                s = MLStripper()
                s.feed(html)
                return s.get_data()
                
            plain_text = strip_tags(memo['content'])
            self.notion_helper.client.blocks.children.append(
                block_id=page['id'],
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": plain_text}}]
                        }
                    }
                ]
            )

    def update_memo(self, memo, page_id):
        print("update_memo:", memo)

        # 预处理内容，处理可能导致问题的格式
        processed_content = self.process_content(memo['content'])
        content_md = markdownify(processed_content)
        # 只更新内容
        content_text = html2text.html2text(processed_content)
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
        
        # 获取标签对应的emoji
        emoji = self.get_emoji_for_tags(memo['tags'])
        
        # 更新页面属性和图标
        page = self.notion_helper.client.pages.update(
            page_id=page_id, 
            properties=properties,
            icon={"type": "emoji", "emoji": emoji}
        )

        # 先清空page的内容，再重新写入
        self.notion_helper.clear_page_content(page["id"])

        try:
            self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])
        except Exception as e:
            print(f"Error uploading content: {e}")
            # 发生错误时，尝试使用纯文本块
            from html.parser import HTMLParser
            
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.strict = False
                    self.convert_charrefs= True
                    self.text = []
                def handle_data(self, d):
                    self.text.append(d)
                def get_data(self):
                    return ''.join(self.text)
                    
            def strip_tags(html):
                s = MLStripper()
                s.feed(html)
                return s.get_data()
                
            plain_text = strip_tags(memo['content'])
            self.notion_helper.client.blocks.children.append(
                block_id=page['id'],
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": plain_text}}]
                        }
                    }
                ]
            )

    # 具体步骤：
    # 1. 调用flomo web端的api从flomo获取数据
    # 2. 轮询flomo的列表数据，调用notion api将数据同步写入到database中的page
    def sync_to_notion(self):
        # 1. 调用flomo web端的api从flomo获取数据
        authorization = os.getenv("FLOMO_TOKEN")
        memo_list = []
        latest_updated_at = "0"

        while True:
            new_memo_list = self.flomo_api.get_memo_list(authorization, latest_updated_at)
            if not new_memo_list:
                break
            memo_list.extend(new_memo_list)
            latest_updated_at = str(int(time.mktime(time.strptime(new_memo_list[-1]['updated_at'], "%Y-%m-%d %H:%M:%S"))))

        # 获取需要同步的标签列表，如果未设置则同步所有标签
        sync_tags = os.getenv("SYNC_TAGS", "")
        if sync_tags:
            # 将标签字符串分割成列表，并去除空格
            sync_tags_list = [tag.strip() for tag in sync_tags.split(',')]
            print(f"只同步包含以下标签的备忘录: {sync_tags_list}")
            # 过滤备忘录列表，只保留包含指定标签的
            filtered_memo_list = []
            for memo in memo_list:
                # 检查备忘录的标签是否与指定标签有交集
                if any(tag in memo['tags'] for tag in sync_tags_list):
                    filtered_memo_list.append(memo)
            memo_list = filtered_memo_list
            print(f"过滤后备忘录数量: {len(memo_list)}")

        # 2. 调用notion api获取数据库存在的记录，用slug标识唯一，如果存在则更新，不存在则写入
        notion_memo_list = self.notion_helper.query_all(self.notion_helper.page_id)
        slug_map = {}
        for notion_memo in notion_memo_list:
            slug_map[notion_utils.get_rich_text_from_result(notion_memo, "slug")] = notion_memo.get("id")

        # 3. 轮询flomo的列表数据
        for memo in memo_list:
            # 3.1 判断memo的slug是否存在，不存在则写入
            # 3.2 防止大批量更新，只更新更新时间为制定时间的数据（默认为7天）
            if memo['slug'] in slug_map.keys():
                # 是否全量更新，默认否
                full_update = os.getenv("FULL_UPDATE", False)
                interval_day = os.getenv("UPDATE_INTERVAL_DAY", 7)
                if not full_update and not is_within_n_days(memo['updated_at'], interval_day):
                    print("is_within_n_days slug:", memo['slug'])
                    continue

                page_id = slug_map[memo['slug']]
                self.update_memo(memo, page_id)
            else:
                self.insert_memo(memo)


if __name__ == "__main__":
    # flomo同步到notion入口
    flomo2notion = Flomo2Notion()
    flomo2notion.sync_to_notion()

    # notionify key
    # secret_IHWKSLUTqUh3A8TIKkeXWePu3PucwHiRwDEcqNp5uT3
