import calendar
import re
from datetime import datetime
from datetime import timedelta

import pendulum


def format_time(time):
    """将秒格式化为 xx时xx分格式"""
    result = ""
    hour = time // 3600
    if hour > 0:
        result += f"{hour}时"
    minutes = time % 3600 // 60
    if minutes > 0:
        result += f"{minutes}分"
    return result


def format_date(date, format="%Y-%m-%d %H:%M:%S"):
    return date.strftime(format)


def timestamp_to_date(timestamp):
    """时间戳转化为date"""
    return datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)


def get_first_and_last_day_of_month(date):
    # 获取给定日期所在月的第一天
    first_day = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在月的最后一天
    _, last_day_of_month = calendar.monthrange(date.year, date.month)
    last_day = date.replace(
        day=last_day_of_month, hour=0, minute=0, second=0, microsecond=0
    )

    return first_day, last_day


def get_first_and_last_day_of_year(date):
    # 获取给定日期所在年的第一天
    first_day = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在年的最后一天
    last_day = date.replace(month=12, day=31, hour=0, minute=0, second=0, microsecond=0)

    return first_day, last_day


def get_first_and_last_day_of_week(date):
    # 获取给定日期所在周的第一天（星期一）
    first_day_of_week = (date - timedelta(days=date.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 获取给定日期所在周的最后一天（星期日）
    last_day_of_week = first_day_of_week + timedelta(days=6)

    return first_day_of_week, last_day_of_week


def str_to_timestamp(date):
    if date == None:
        return 0
    dt = pendulum.parse(date)
    # 获取时间戳
    return int(dt.timestamp())


def truncate_string(s, length=30):
    # 正则表达式匹配标点符号或换行符
    pattern = re.compile(r'[，。！？；：,.!?;:\n]')

    # 查找第一个匹配的位置
    match = pattern.search(s)

    if match:
        # 如果找到匹配，并且位置在限制长度之前，则在该位置截取
        end_pos = match.start() if match.start() < length else length
    else:
        # 如果没有找到匹配，则截取前30个字符
        end_pos = length

    return s[:end_pos]


def is_within_n_days(target_date_str, n):
    # 将目标日期字符串转换为 datetime 对象
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d %H:%M:%S')

    # 获取当前时间
    now = datetime.now()

    # 计算 n 天前的时间
    n_days_ago = now - timedelta(days=n)

    # 判断目标日期是否在 n 天内
    return n_days_ago <= target_date <= now