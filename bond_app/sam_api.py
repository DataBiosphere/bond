import json
import logging
import requests

from werkzeug import exceptions


class SamApi:
    def __init__(self, base_url, cache_api):
        self.base_url = base_url
        self.cache_api = cache_api

    def user_info(self, user_info):
        """
        Calls sam GET /register/user/v1 api
        :param user_info: user info from Google
        :return: dict with userSubjectId and userEmail keys or else None if user does not exist in sam
        """
        sam_user_info = self.cache_api.get(namespace='SamApi', key=user_info.id)
        if sam_user_info is None:
            headers = {'Authorization': 'Bearer ' + user_info.token}
            result = requests.get(url=self.base_url + '/register/user/v2/self/info', headers=headers)
            if result.status_code == 200:
                sam_user_info = json.loads(result.content)
                self.cache_api.add(namespace='SamApi', key=user_info.id, value=sam_user_info, expires_in=60*60)
            else:
                logging.info("sam status code {}, error body {}".format(result.status_code, result.content))
                if result.status_code == 404:
                    return None
                raise exceptions.InternalServerError("sam status code {}, error body {}".format(result.status_code, result.content))
        else:
            logging.debug("sam user id cache hit for id %s", user_info.id)

        return sam_user_info

    def status(self):
        """
        Tests the connection to sam
        :return: 2 values: boolean ok or not, status message if not ok
        """
        try:
            result = requests.get(url=self.base_url + "/status")
            if result.status_code // 100 != 2:
                return False, "sam status code {}, error body {}".format(result.status_code, result.content)
            else:
                return True, ""
        except Exception as e:
            return False, str(e)


class SamKeys:
    USER_ID_KEY = "userSubjectId"
    USER_EMAIL_KEY = "userEmail"
    USER_ENABLED_KEY = "enabled"
