import re, os
from dotenv import load_dotenv
from notion_client import Client
from notionify.Parser.md2block import read_file, read_file_content


class Md2NotionUploader:
    image_host_object = None
    local_root = "markdown_notebook"

    def __init__(self, image_host='aliyun', auth=None):
        self.image_host = image_host
        self.auth = auth

    def _get_onedrive_client(self):
        # 待实现
        pass
        # self.onedrive = self.image_host_object
        # if self.onedrive is None and self.onedrive_client_id is not None:
        #     from ImageHosting.Onedrive import Onedrive_Hosting
        #     self.onedrive = Onedrive_Hosting(self.onedrive_client_id, self.client_secret)
        #     if self.auth: self.onedrive.initilize()
        #     self.onedrive._obtain_drive()
        # self.image_host_object = self.onedrive
        # return self.image_host_object

    def _get_smms_client(self):
        # 待实现
        pass
        # self.smms = self.image_host_object
        # if self.smms is None and self.smms_token is not None:
        #     from ImageHosting.SMMS import SMMS_Hosting
        #     self.smms = SMMS_Hosting(token=self.smms_token)
        # self.image_host_object = self.smms
        # return self.image_host_object

    @staticmethod
    def split_text(text):
        text = re.sub(r'<img\s+src="(.*?)"\s+alt="(.*?)"\s+.*?/>', r'![\2](\1)', text)
        out = []
        double_dollar_parts = re.split(r'(\$\$.*?\$\$)', text, flags=re.S)

        for part in double_dollar_parts:
            if part.startswith('$$') and part.endswith('$$'):
                part = part.replace('{align}', '{aligned}')
                part = part.replace('\\\n', '\\\\\n')
                out.append(part)
            else:
                image_parts = re.split(r'(!\[.*?\]\(.*?\))', part)
                out.extend(image_parts)
        out = [t for t in out if t.strip() != '']
        return out

    def blockparser(self, s, _type="paragraph"):
        parts = self.split_text(s)
        result = []
        for part in parts:
            if part.startswith('$$'):
                expression = part.strip('$$')
                result.append({
                    "equation": {
                        "expression": expression.strip()
                    }
                })
            elif part.startswith('![') and '](' in part:
                caption, url = re.match(r'!\[(.*?)\]\((.*?)\)', part).groups()
                # 处理URL中可能的转义字符
                url = url.replace('\\', '')
                # 确保URL格式正确
                if not url.startswith(('http://', 'https://')):
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        url = 'https:/' + url
                
                print(f"Processing image URL: {url}")
                url = self.convert_to_oneline_url(url)
                result.append({
                    "image": {
                        "caption": [],  # caption,
                        "type": "external",
                        "external": {
                            "url": url
                        }  ##'embed': {'caption': [],'url': url} #<-- for onedrive
                    }
                })
            else:
                result.append({
                    _type: {
                        "rich_text": self.sentence_parser(part)
                    }
                })

        return result

    @staticmethod
    def is_balanced(s):
        single_dollar_count = s.count('$')
        double_dollar_count = s.count('$$')

        return single_dollar_count % 2 == 0 and double_dollar_count % 2 == 0

    @staticmethod
    def parse_annotations(text):
        annotations = {
            'bold': False,
            'italic': False,
            'strikethrough': False,
            'underline': False,
            'code': False,
            'color': 'default'
        }

        # Add bold
        if '**' in text or '__' in text:
            annotations['bold'] = True
            text = re.sub(r'\*\*|__', '', text)

        # Add italic
        if '*' in text or '_' in text:
            annotations['italic'] = True
            text = re.sub(r'\*|_', '', text)

        # Add strikethrough
        if '~~' in text:
            annotations['strikethrough'] = True
            text = text.replace('~~', '')

        if '`' in text:
            annotations['code'] = True
            text = text.replace('`', '')

        return annotations, text

    def convert_to_oneline_url(self, url):
        # check the url is local. (We assume it in Onedrive File)
        # leanote的全部转为远程图片，不需要转换
        if "http" in url: return url
        if (".png" not in url) and (".jpg" not in url) and (".svg" not in url): return url
        ## we will locate the Onedrive image
        if self.image_host == 'onedrive':
            return self.convert_to_oneline_url_onedrive(url)
        elif self.image_host == 'smms':
            return self.convert_to_oneline_url_smms(url)
        elif self.image_host == 'aliyun':
            return self.convert_to_oneline_url_aliyun(url)
        elif self.image_host == 'direct':
            # 直接使用URL，不做转换
            return url
        else:
            raise Exception(f"Invalid Image Hosting: {self.image_host}")

    def convert_to_oneline_url_onedrive(self, url):
        if os.path.exists(url):
            # the script path is at root
            path = os.path.abspath(url)
            drive, path = os.path.splitdrive(path)
            onedrive_path = '/markdown_notebook' + path.split('markdown_notebook', 1)[1]
        else:
            # the script path is not at root. then we whould use the self.local_root
            url = url.strip('.').strip('/')
            onedrive_path = f'/{self.local_root}/{url}'
        onedrive = self._get_onedrive_client()
        url = onedrive.get_link_by_path(onedrive_path)
        # url = onedrive.get_final_link_by_share(url)
        return url

    def convert_to_oneline_url_aliyun(self, url):
        pass
        # if os.path.exists(url):
        #     aliyun = self._get_aliyun_client()
        #     # 必须以二进制的方式打开文件，因为需要知道文件包含的字节数。
        #     with open(url, 'rb') as file_obj:
        #         res = aliyun.put_object(object_name, file_obj)
        #
        # return url

    def convert_to_oneline_url_smms(self, url):
        # if the url is relative path, the root dir should be declared
        smms = self._get_smms_client()

        smms.upload_image(os.path.join(self.local_root, url))
        return smms.url

    def sentence_parser(self, s):
        # if not self.is_balanced(s):
        #     raise ValueError("Unbalanced math delimiters in the input string.")

        # Split string by inline math and markdown links
        parts = re.split(r'(\$.*?\$|\[.*?\]\(.*?\))', s)
        result = []

        for part in parts:
            if part.startswith('$'):
                expression = part.strip('$')
                result.append({
                    "type": "equation",
                    "equation": {
                        "expression": expression
                    }
                })
            elif part.startswith('[') and '](' in part:
                # Process style delimiters before processing link
                style_parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_|~~.*?~~|`.*?`)', part)
                for style_part in style_parts:
                    annotations, clean_text = self.parse_annotations(style_part)
                    if clean_text.startswith('[') and '](' in clean_text:
                        link_text, url = re.match(r'\[(.*?)\]\((.*?)\)', clean_text).groups()

                        result.append({
                            "type": "text",
                            "text": {
                                "content": link_text,
                                "link": {
                                    "url": url
                                }
                            },
                            "annotations": annotations,
                            "plain_text": link_text,
                            "href": url
                        })
                    elif clean_text:
                        result.append({
                            "type": "text",
                            "text": {
                                "content": clean_text,
                                "link": None
                            },
                            "annotations": annotations,
                            "plain_text": clean_text,
                            "href": None
                        })
            else:
                # Split text by style delimiters
                style_parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_|~~.*?~~|`.*?`)', part)
                for style_part in style_parts:
                    annotations, clean_text = self.parse_annotations(style_part)
                    if clean_text:
                        result.append({
                            "type": "text",
                            "text": {
                                "content": clean_text,
                                "link": None
                            },
                            "annotations": annotations,
                            "plain_text": clean_text,
                            "href": None
                        })

        return result

    def convert_to_raw_cell(self, line):
        children = {"table_row": {"cells": []}}
        for content in line:
            # print(uploader.blockparser(content,'text'))
            cell_json = self.sentence_parser(content)
            children["table_row"]["cells"].append(cell_json)
        return children

    def convert_table(self, _dict):

        parents_dict = {
            'table_width': 3,
            'has_column_header': False,
            'has_row_header': False,
            'children': []
        }
        assert 'rows' in _dict
        if 'schema' in _dict and len(_dict['schema']) > 0:
            parents_dict['has_column_header'] = True
            line = [v['name'] for v in _dict['schema'].values()]
            parents_dict['children'].append(self.convert_to_raw_cell(line))

        width = 0
        for line in _dict['rows']:
            width = max(len(line), width)
            parents_dict['children'].append(self.convert_to_raw_cell(line))
        parents_dict['table_width'] = width
        return [{'table': parents_dict}]

    def convert_image(self, _dict):
        url = _dict['source']
        url = self.convert_to_oneline_url(url)
        assert url is not None
        return [{"image": {"caption": [], "type": "external",
                           "external": {"url": url}
                           }
                 }]

    def uploadBlock(self, blockDescriptor, notion, page_id, mdFilePath=None, imagePathFunc=None):
        """
        Uploads a single blockDescriptor for NotionPyRenderer as the child of another block
        and does any post processing for Markdown importing
        @param {dict} blockDescriptor A block descriptor, output from NotionPyRenderer
        @param {NotionBlock} blockParent The parent to add it as a child of
        @param {string} mdFilePath The path to the markdown file to find images with
        @param {callable|None) [imagePathFunc=None] See upload()

        @todo Make mdFilePath optional and don't do searching if not provided
        """
        new_name_map = {
            'text': 'paragraph',
            'bulleted_list': 'bulleted_list_item',
            'header': 'heading_1',
            'sub_header': 'heading_2',
            'sub_sub_header': 'heading_3',
            'numbered_list': 'numbered_list_item'
        }
        blockClass = blockDescriptor["type"]

        old_name = blockDescriptor['type']._type
        new_name = new_name_map[old_name] if old_name in new_name_map else old_name

        if new_name == 'collection_view':
            # this is a table
            content_block = self.convert_table(blockDescriptor)
        elif new_name == 'image':
            # this is a table
            content_block = self.convert_image(blockDescriptor)
        elif 'title' in blockDescriptor:
            content = blockDescriptor['title']
            content_block = self.blockparser(content, new_name)
        elif new_name == 'code':
            language = blockDescriptor['language']
            content = blockDescriptor['title_plaintext']
            content_block = self.blockparser(content, new_name)
            if not content_block:
                return
            content_block[0]['code']['language'] = language.lower()
        else:
            content_block = [{new_name: {}}]
        response = notion.blocks.children.append(block_id=page_id, children=content_block)

        blockChildren = None
        if "children" in blockDescriptor:
            blockChildren = blockDescriptor["children"]
        if blockChildren:
            child_id = response['results'][-1]['id']
            for childBlock in blockChildren:
                ### firstly create one than
                self.uploadBlock(childBlock, notion, child_id, mdFilePath, imagePathFunc)

    def uploadSingleFile(self, notion, filepath, page_id="",start_line = 0):
        if os.path.exists(filepath):
            # get the notionify style block information
            notion_blocks = read_file(filepath)
            for i,content in enumerate(notion_blocks):
                if i < start_line:continue
                print(f"uploading line {i},............", end = '')
                self.uploadBlock(content, notion, page_id)
                print('done!')
        else:
            print(f"file {filepath} not found")

    def uploadSingleFileContent(self, notion, content, page_id="", start_line = 0):
        if content is not None:
            # get the notionify style block information
            notion_blocks = read_file_content(content)
            for i,content in enumerate(notion_blocks):
                if i < start_line:continue
                print(f"uploading line {i},............", end = '')
                # q:'uploader' is not defined in the function?  a: uploader is the instance of the class
                self.uploadBlock(content, notion, page_id)
                print('done!')
        else:
            print(f"content is None")


if __name__ == '__main__':
    load_dotenv()
    # get your smms token from  https://sm.ms/home
    ## you can also use usename and password. See the code in ImageHosting/SMMS.py
    # you can also use use other image host, such as imgur, qiniu, upyun, github, gitee, aliyun, tencent, jd, netease, huawei, aws, imgbb, smms, v2ex, weibo, weiyun, zimg
    ## the onedrive image hosting is supported, but the onedrive can only provide framed view which is not a direct link to the image.
    auth = {
        'aliyun': {
            'access_key_id': os.getenv("ALIYUN_OSS_ACCESS_KEY_ID"),
            'access_key_secret:': os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET"),
            'endpoint': os.getenv("ALIYUN_OSS_ENDPOINT"),
            'bucket': os.getenv("ALIYUN_OSS_BUCKET")
        }
    }
    uploader = Md2NotionUploader(image_host='aliyun', auth=auth)
    key = os.getenv("NOTION_INTEGRATION_SECRET")
    notion = Client(auth=os.getenv("NOTION_INTEGRATION_SECRET"))
    uploader.uploadSingleFile(
        notion,
        "/usr/local/var/sideline/notionify/notionify-transfer/notionify-transfer-leanote/6107bb66ab64416caa000a0f.md",
        "ee6ea436f6ff4d2fb0c33c3fa01629ae"
    )
