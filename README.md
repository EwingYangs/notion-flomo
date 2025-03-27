# 官网开启一键同步

如果你觉得部署繁琐，可以直接使用NotesToNotion
[NotesToNotion](https://memohub.notionify.net)

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

### 2024年更新
- 修复了rich_text数组为空导致索引错误的问题
- 修复了Notion选项中不允许使用逗号的问题（将逗号自动替换为破折号）
- 优化了错误处理机制

## 注意事项

1. Notion的select和multi_select选项中不允许使用逗号，本工具会自动将逗号替换为破折号
2. 默认情况下，只会同步最近7天内更新的备忘录
3. 可以通过设置环境变量`FULL_UPDATE=True`来触发全量更新
4. 工作流默认每3小时自动运行一次
