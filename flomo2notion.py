import os
import random
import time

import html2text
from markdownify import markdownify

from flomo.flomo_api import FlomoApi
from notionify import notion_utils
from notionify.md2notion import Md2NotionUploader
from notionify.notion_cover_list import cover
from notionify.notion_helper import NotionHelper
from utils import truncate_string, is_within_n_days


class Flomo2Notion:
    def __init__(self):
        self.flomo_api = FlomoApi()
        self.notion_helper = NotionHelper()
        self.uploader = Md2NotionUploader()

    def insert_memo(self, memo):
        print("insert_memo:", memo)
        
        # 处理 None 内容
        if memo['content'] is None:
            # 如果有文件，将它们作为内容
            if memo.get('files') and len(memo['files']) > 0:
                content_md = "# 图片备忘录\n\n"
                for file in memo['files']:
                    if file.get('url'):
                        # 清理 URL 中的反引号和多余空格
                        clean_url = file['url'].strip().strip('`')
                        clean_name = file.get('name', '图片').strip().strip('`')
                        content_md += f"![{clean_name}]({clean_url})\n\n"
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
        print(f"Random element: {random_cover}")
    
        page = self.notion_helper.client.pages.create(
            parent=parent,
            icon=notion_utils.get_icon("https://www.notion.so/icons/target_red.svg"),
            cover=notion_utils.get_icon(random_cover),
            properties=properties,
        )
    
        # 在page里面添加content
        self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])

    def update_memo(self, memo, page_id):
        print("update_memo:", memo)
    
        # 处理 None 内容
        if memo['content'] is None:
            # 如果有文件，将它们作为内容
            if memo.get('files') and len(memo['files']) > 0:
                content_md = "# 图片备忘录\n\n"
                for file in memo['files']:
                    if file.get('url'):
                        content_md += f"![{file.get('name', '图片')}]({file['url']})\n\n"
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
        page = self.notion_helper.client.pages.update(page_id=page_id, properties=properties)
    
        # 先清空page的内容，再重新写入
        self.notion_helper.clear_page_content(page["id"])
    
        self.uploader.uploadSingleFileContent(self.notion_helper.client, content_md, page['id'])

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
