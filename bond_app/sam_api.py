import json
import logging
import requests

from werkzeug import exceptions


class SamApi:
    def __init__(self, base_url):
        self.base_url = base_url

    def user_info(self, access_token):
        """
        Calls sam GET /register/user/v1 api
        :param access_token: oauth access token
        :return: dict with userSubjectId and userEmail keys or else None if user does not exist in sam
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = requests.get(url=self.base_url + '/register/user/v2/self/info', headers=headers)
        if result.status_code == 200:
            return json.loads(result.content)
        logging.info("sam status code {}, error body {}".format(result.status_code, result.content))
        if result.status_code == 404:
            return None
        raise exceptions.InternalServerError("sam status code {}, error body {}".format(result.status_code, result.content))

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
