from google.appengine.api import urlfetch
import json
import endpoints


class SamApi:
    def __init__(self, base_url):
        self.base_url = base_url

    def user_info(self, access_token):
        """
        Calls sam GET /register/user/v1 api
        :param access_token: oauth access token
        :return: dict with userSubjectId and userEmail keys or None if user does not exist in sam
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = urlfetch.fetch(url=self.base_url + '/register/user/v1?userDetailsOnly=true', headers=headers)
        if result.status_code == 200:
            return json.loads(result.content)["userInfo"]
        elif result.status_code == 404:
            return None
        else:
            raise endpoints.InternalServerErrorException("sam status code {}, error body {}".format(result.status_code, result.content))

    def status(self):
        """
        Tests the connection to sam
        :return: 2 values: boolean ok or not, status message if not ok
        """
        try:
            result = urlfetch.fetch(url=self.base_url + "/status")
            if result.status_code // 100 != 2:
                return False, "sam status code {}, error body {}".format(result.status_code, result.content)
            else:
                return True, ""
        except Exception as e:
            return False, e.message


class SamKeys:
    USER_ID_KEY = "userSubjectId"
    USER_EMAIL_KEY = "userEmail"
