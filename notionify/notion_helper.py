import logging
import os

from dotenv import load_dotenv
from notion_client import Client
from retrying import retry

from notionify.notion_utils import extract_page_id

load_dotenv()


class NotionHelper:
    database_id_dict = {}
    heatmap_block_id = None

    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"), log_level=logging.ERROR)
        self.page_id = extract_page_id(os.getenv("NOTION_PAGE"))
        self.__cache = {}

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def clear_page_content(self, page_id):
        # 获取页面的块内容
        result = self.client.blocks.children.list(page_id)
        if not result:
            return

        blocks = result.get('results')

        for block in blocks:
            block_id = block['id']
            # 删除每个块
            self.client.blocks.delete(block_id)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def update_book_page(self, page_id, properties):
        return self.client.pages.update(page_id=page_id, properties=properties)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def update_page(self, page_id, properties, cover):
        return self.client.pages.update(
            page_id=page_id, properties=properties, cover=cover
        )

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def create_page(self, parent, properties, icon):
        return self.client.pages.create(parent=parent, properties=properties, icon=icon)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def create_book_page(self, parent, properties, icon):
        return self.client.pages.create(
            parent=parent, properties=properties, icon=icon, cover=icon
        )

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def query(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        return self.client.databases.query(**kwargs)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_block_children(self, id):
        response = self.client.blocks.children.list(id)
        return response.get("results")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def append_blocks(self, block_id, children):
        return self.client.blocks.children.append(block_id=block_id, children=children)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def append_blocks_after(self, block_id, children, after):
        return self.client.blocks.children.append(
            block_id=block_id, children=children, after=after
        )

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def delete_block(self, block_id):
        return self.client.blocks.delete(block_id=block_id)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def query_all(self, database_id):
        """获取database中所有的数据"""
        results = []
        has_more = True
        start_cursor = None
        while has_more:
            response = self.client.databases.query(
                database_id=database_id,
                start_cursor=start_cursor,
                page_size=100,
            )
            start_cursor = response.get("next_cursor")
            has_more = response.get("has_more")
            results.extend(response.get("results"))
        return results


if __name__ == "__main__":
    notion_helper = NotionHelper()
    notion_helper.query()
