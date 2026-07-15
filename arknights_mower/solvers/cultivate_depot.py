import datetime
import json

import requests

from arknights_mower.utils import config
from arknights_mower.utils.log import logger
from arknights_mower.utils.path import get_path
from arknights_mower.utils.skland import (
    get_binding_list,
    get_cred_by_token,
    get_sign_header,
    header,
    log,
    skland_cache,
)


class cultivate:
    def __init__(self):
        self.record_path = get_path("@app/tmp/cultivate.json")
        self.reward = []
        self.sign_token = ""
        self.all_recorded = True

    def start(self):
        if not config.conf.skland_info:
            return
        item = config.conf.skland_info[0]

        # Reuse existing credential if already available (e.g. from a previous call)
        if header["cred"]:
            # 复用凭据时从缓存恢复 sign_token（新实例默认值为空字符串）
            cached = skland_cache.get(item.account)
            if cached:
                self.sign_token = cached["sign_token"]
            logger.debug("cultivate: reusing existing credential")
        else:
            cred_resp = get_cred_by_token(log(item))
            self.save_param(cred_resp)
            # Share credential so PlayerInfoClient can reuse via skland_cache
            skland_cache[item.account] = {
                "cred": cred_resp["cred"],
                "sign_token": cred_resp["token"],
                "updated_at": datetime.datetime.now(datetime.timezone.utc),
            }

        for i in get_binding_list(self.sign_token):
            if i.get("gameId") == 1 and item.cultivate_select == i.get("isOfficial"):
                body = {"gameId": 1, "uid": i.get("uid")}
                ingame = f"https://zonai.skland.com/api/v1/game/cultivate/player?uid={i.get('uid')}"
                resp = requests.get(
                    ingame,
                    headers=get_sign_header(ingame, "get", body, self.sign_token),
                    timeout=30,
                ).json()
                self.record_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.record_path, "w", encoding="utf-8") as file:
                    json.dump(resp, file, ensure_ascii=False, indent=4)

    def save_param(self, cred_resp):
        header["cred"] = cred_resp["cred"]
        self.sign_token = cred_resp["token"]
