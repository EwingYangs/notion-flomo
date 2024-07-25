import hashlib


def _ksort(d):
    return dict(sorted(d.items()))


def getSign(e):
    e = _ksort(e)
    t = ""
    for i in e:
        o = e[i]
        if o is not None and (o or o == 0):
            if isinstance(o, list):
                o.sort(key=lambda x: x if x else '')
                for item in o:
                    t += f"{i}[]={item}&"
            else:
                t += f"{i}={o}&"
    t = t[:-1]
    return c(t + "dbbc3dd73364b4084c3a69346e0ce2b2")


def c(t):
    return hashlib.md5(t.encode('utf-8')).hexdigest()


# 测试数据
# e = {
#     "api_key": "flomo_web",
#     "app_version": "4.0",
#     "platform": "web",
#     "timestamp": 1720147723,
#     "webp": "1"
# }

e = {
    "limit": 200,
    "latest_updated_at": 0,
    "tz": "8:0",
    "timestamp": 1720075310,
    "api_key": "flomo_web",
    "app_version": "4.0",
    "platform": "web",
    "webp": "1"
}

print(getSign(e))
