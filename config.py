# 要同步的标签列表，多个标签用逗号分隔
# 例如：SYNC_TAGS = "得到,读书笔记"
# 如果不设置（空字符串），将同步所有备忘录（包括没有标签的）
# 使用包含匹配方式，例如设置"读书"会匹配"读书笔记"、"读书心得"等包含该关键词的标签
SYNC_TAGS = "看书,创业想法,精进技巧"

# 是否清理不符合标签条件的记录
# 设置为True将删除Notion中不符合当前标签条件的记录
# 默认为False
CLEAN_UNMATCHED = True

# 是否进行全量更新
# 设置为True将同步所有符合条件的备忘录，不考虑更新时间
# 默认为False，只同步最近一段时间内更新的备忘录
# 适合首次运行或需要完全重建Notion数据库时使用
FULL_UPDATE = False

# 更新间隔天数
# 指定只同步最近多少天内更新的备忘录
# 默认为7，表示只同步最近7天内更新的备忘录
# 当FULL_UPDATE=True时此设置无效
UPDATE_INTERVAL_DAY = 7

# 标签对应的emoji映射
# 可以根据需要自定义更多标签的emoji映射
# 当备忘录包含多个标签时，系统会使用第一个标签来确定emoji
# 如果没有匹配到预设的标签，会使用默认的📌图标
TAG_EMOJI_MAP = {
    "重要": "🔥",
    "工作": "💼",
    "学习": "📚",
    "阅读": "📖",
    "笔记": "📝",
    "计划": "📅",
    "想法": "💡",
    "日记": "📔",
    "健康": "💪",
    "旅行": "✈️",
    "美食": "🍔",
    "电影": "🎬",
    "创业想法": "💡",
    "精进技巧": "💪",
    "看书": "📖"
}

# 默认emoji，当没有匹配的标签时使用
DEFAULT_EMOJI = "📌" 