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
            return json.load(result.content)
        elif result.status_code == 404:
            return None
        else:
            raise endpoints.InternalServerErrorException("sam status code {}, error body {}".format(result.status_code, result.content))