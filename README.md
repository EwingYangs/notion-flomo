# 官网开启一键同步
# 将flomo同步到Notion

本项目通过Github Action每天定时同步flomo到Notion。

预览效果：

[flomo2notion列表页面](https://www.notion.so/image/https%3A%2F%2Fprod-files-secure.s3.us-west-2.amazonaws.com%2Fd01f9e1b-37be-4e62-ba09-3e4835a67760%2F7d8e606e-2bb2-48e0-84fb-e8fe4f70ae5b%2FUntitled.png?table=block&id=df77b666-0f2b-4d96-848e-a0193759c0e3&t=df77b666-0f2b-4d96-848e-a0193759c0e3&width=840.6771240234375&cache=v2)

[flomo2notion详情页面](https://www.notion.so/image/https%3A%2F%2Fprod-files-secure.s3.us-west-2.amazonaws.com%2Fd01f9e1b-37be-4e62-ba09-3e4835a67760%2F8daf2284-aedf-4e04-8f55-9f1fe409e4cc%2FUntitled.png?table=block&id=31fb72fd-0b40-4ae1-82f5-9de52e1aeed1&t=31fb72fd-0b40-4ae1-82f5-9de52e1aeed1&width=2078&cache=v2)

## 使用教程

[flomo2notion教程](https://blog.notionedu.com/article/0d91c395-d74a-4ce4-a219-afdca8e90c92#52ef8ad045d84e0c900ecbe529ce3653)

## 更新日志

### 2023年更新
- 初始版本发布

### 2025年更新
- 修复了rich_text数组为空导致索引错误的问题
- 修复了Notion选项中不允许使用逗号的问题（将逗号自动替换为破折号）
- 修复了特殊格式（如[OK][捂脸]等表情符号）导致Markdown解析错误的问题
- 添加了错误处理机制，当Markdown解析失败时会尝试使用纯文本方式显示内容
- 优化了错误处理机制
- 添加了按标签过滤功能，允许用户只同步特定标签的备忘录
- 移除了随机背景图片，改为根据标签自动设置emoji图标
- 修复了图片同步问题，现在flomo中的图片可以正确同步到Notion
- 增加了清理不符合标签条件记录的功能，使Notion数据库保持整洁
- 优化了标签匹配逻辑，确保无标签记录不会被同步
- 将标签过滤配置移至本地配置文件，方便版本控制和修改

## 注意事项

1. Notion的select和multi_select选项中不允许使用逗号，本工具会自动将逗号替换为破折号
2. 默认情况下，只会同步最近7天内更新的备忘录
3. 可以通过设置环境变量`FULL_UPDATE=True`来触发全量更新
4. 工作流默认每12小时自动运行一次
5. 对于包含特殊格式（如表情符号等）的内容，会进行预处理以避免解析错误
6. 要同步特定标签的备忘录，请在 `config.py` 文件中设置 `SYNC_TAGS` 变量，多个标签用逗号分隔，例如：`SYNC_TAGS = "重要,工作,学习"`
7. 设置环境变量`CLEAN_UNMATCHED=true`可以删除不符合标签条件的记录，保持Notion数据库整洁

## 高级用法

### 配置文件设置

本工具使用 `config.py` 文件来存储本地配置：

1. **SYNC_TAGS**：要同步的标签列表
   - 在 `config.py` 文件中设置 `SYNC_TAGS` 变量
   - 多个标签用逗号分隔，例如：`SYNC_TAGS = "得到,读书笔记"`
   - 如果设置为空字符串，将同步所有备忘录（包括没有标签的）
   - 使用包含匹配方式，例如设置`读书`会匹配"读书笔记"、"读书心得"等包含该关键词的标签

### GitHub Actions环境变量配置

本工具通过GitHub Actions自动运行，需要在GitHub仓库中设置以下环境变量（Secrets）：

#### 必需的环境变量

1. **NOTION_TOKEN**：Notion API的访问令牌
   - 在[Notion开发者页面](https://www.notion.so/my-integrations)创建一个集成，获取令牌

2. **NOTION_PAGE**：Notion数据库的URL或ID
   - 复制Notion数据库页面的URL，或者仅复制URL中的数据库ID部分

3. **FLOMO_TOKEN**：Flomo的API访问令牌
   - 从Flomo网页版获取

#### 可选的环境变量

1. **CLEAN_UNMATCHED**：是否清理不符合标签条件的记录
   - 设置为`true`将删除Notion中不符合当前标签条件的记录
   - 默认为`false`
   - 建议与`SYNC_TAGS`配合使用，确保只保留符合条件的记录

2. **FULL_UPDATE**：是否进行全量更新
   - 设置为`true`将同步所有符合条件的备忘录，不考虑更新时间
   - 默认为`false`，只同步最近一段时间内更新的备忘录
   - 适合首次运行或需要完全重建Notion数据库时使用

3. **UPDATE_INTERVAL_DAY**：更新间隔天数
   - 指定只同步最近多少天内更新的备忘录
   - 默认为`7`，表示只同步最近7天内更新的备忘录
   - 当`FULL_UPDATE=true`时此设置无效

#### 设置方法

1. 在GitHub仓库页面，进入"Settings" > "Secrets and variables" > "Actions"
2. 点击"New repository secret"按钮
3. 添加上述环境变量，填入对应的值
4. 点击"Add secret"保存

示例配置：
- `NOTION_TOKEN`: `secret_abcdefg123456789`
- `NOTION_PAGE`: `https://www.notion.so/1234578936e80ffa215cd9fbf1fa332`
- `FLOMO_TOKEN`: `123456|abcdefg123456789`
- `CLEAN_UNMATCHED`: `true`
- `FULL_UPDATE`: `true`
- `UPDATE_INTERVAL_DAY`: `30`

### 按标签过滤同步

如果你只想同步包含特定标签的备忘录，可以在GitHub Actions的环境变量中设置`SYNC_TAGS`：

1. 在GitHub仓库页面，进入"Settings" > "Secrets and variables" > "Actions"
2. 点击"New repository secret"按钮
3. 名称填入`SYNC_TAGS`，值填入你想要同步的标签，多个标签用逗号分隔，例如：`日记,读书笔记,重要`
4. 点击"Add secret"保存

这样，只有包含这些标签的flomo备忘录才会被同步到Notion中，其他备忘录将被忽略。

系统使用包含匹配方式：如果备忘录的标签包含你指定的任何标签关键词，该备忘录就会被同步。例如，设置`SYNC_TAGS=读书,工作`，则标签为"读书笔记"、"工作计划"等包含这些关键词的备忘录都会被同步。没有标签的备忘录不会被同步。

### 清理不符合标签条件的记录

如果你想保持Notion数据库的整洁，只保留符合标签条件的记录，可以设置环境变量`CLEAN_UNMATCHED=true`：

1. 在GitHub仓库页面，进入"Settings" > "Secrets and variables" > "Actions"
2. 点击"New repository secret"按钮
3. 名称填入`CLEAN_UNMATCHED`，值填入`true`
4. 点击"Add secret"保存

启用此功能后，系统会在同步过程中：
- 识别Notion中不符合当前标签条件的记录（包括在flomo中已删除的记录，或者标签不匹配的记录）
- 将这些记录归档（在Notion中相当于删除）
- 保持数据库中只有符合条件的记录

**注意**：启用此功能前请确保已正确设置`SYNC_TAGS`，并且已备份重要数据，以防意外删除。

### 自定义标签对应的emoji图标

系统已内置了常用标签对应的emoji映射：
- 重要：🔥
- 工作：💼
- 学习：📚
- 阅读：📖
- 笔记：📝
- 计划：📅
- 想法：💡
- 日记：📔
- 健康：💪
- 旅行：✈️
- 美食：🍔
- 电影：🎬
- 音乐：🎵
- 项目：📊
- 问题：❓
- 解决：✅

如果需要自定义更多标签的emoji映射，可以修改代码中的`TAG_EMOJI_MAP`字典。当备忘录包含多个标签时，系统会使用第一个标签来确定emoji。如果没有匹配到预设的标签，会使用默认的📌图标。

### 图片同步

系统现在支持将flomo中的图片同步到Notion：

1. 同步过程中会处理图片链接，确保格式正确，能够在Notion中正确显示
2. 图片会作为外部链接嵌入到Notion页面中，而不是上传到Notion
3. 如果遇到图片显示问题，可能是因为图片源站点设置了防盗链，这种情况下图片可能无法在Notion中显示
