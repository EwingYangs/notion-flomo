import time

import requests

from flomo.flomo_sign import getSign

FLOMO_DOMAIN = "https://flomoapp.com"
MEMO_LIST_URL = FLOMO_DOMAIN + "/api/v1/memo/updated/"

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'origin': 'https://v.flomoapp.com',
    'priority': 'u=1, i',
    'referer': 'https://v.flomoapp.com/',
    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}


class FlomoApi:
    def __int__(self):
        pass

    def get_memo_list(self, user_authorization, latest_updated_at="0"):
        # 获取当前时间
        current_timestamp = int(time.time())

        latest_updated_at = str(int(latest_updated_at) + 1)

        # 构造参数
        params = {
            'limit': '200',
            'latest_updated_at': latest_updated_at,
            'tz': '8:0',
            'timestamp': current_timestamp,
            'api_key': 'flomo_web',
            'app_version': '4.0',
            'platform': 'web',
            'webp': '1'
        }

        # 获取签名
        params['sign'] = getSign(params)
        HEADERS['authorization'] = f'Bearer {user_authorization}'

        response = requests.get(MEMO_LIST_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            # 网络或者服务器错误
            print('get_memo_list http error:' + response.text)
            return

        response_json = response.json()
        if response_json['code'] != 0:
            print("get_memo_list business error:" + response_json['message'])
            return

        return response_json['data']

    def get_login_wechat_qrcode(self):
        pass

    def get_user_auth(self):
        pass


if __name__ == "__main__":
    flomo_api = FlomoApi()
    authorization = 'Bearer 7505209|Lf9wvt5JKIFBS4zfayw61X3MuoH1nS5xcPMB3fqS'
    memo_list = flomo_api.get_memo_list(authorization)
    print(memo_list)
