from google.appengine.api import urlfetch
from werkzeug import exceptions


class FenceApi:
    def __init__(self, base_url):
        self.credentials_google_url = base_url + "/user/credentials/google"
        self.revoke_url = base_url + "/user/oauth2/revoke"
        self.delete_service_account_url = base_url + "/user/credentials/google/"
        self.status_url = base_url + "/user/.well-known/openid-configuration"

    def get_credentials_google(self, access_token):
        """
        Calls fence POST /user/credentials/google api
        :param access_token: oauth access token
        :return: service account key json
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = urlfetch.fetch(url=self.credentials_google_url, headers=headers, method=urlfetch.POST)
        if result.status_code // 100 == 2:
            return result.content
        else:
            raise exceptions.InternalServerError("fence status code {}, error body {}".format(result.status_code, result.content))

    def delete_credentials_google(self, access_token, key_id):
        """
        Calls fence DELETE /user/credentials/google/key_id api
        :param access_token: oauth access token
        :param key_id: key_id to delete
        :return: service account key json
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = urlfetch.fetch(url=self.delete_service_account_url + key_id, headers=headers, method=urlfetch.DELETE)
        if result.status_code // 100 != 2:
            raise exceptions.InternalServerError("fence status code {}, error body {}".format(result.status_code, result.content))

    def revoke_refresh_token(self, refresh_token):
        result = urlfetch.fetch(url=self.revoke_url, method=urlfetch.POST, payload=refresh_token)
        if result.status_code // 100 != 2:
            raise exceptions.InternalServerError("fence status code {}, error body {}".format(result.status_code, result.content))

    def status(self):
        """
        Tests the connection to fence
        :return: 2 values: boolean ok or not, status message if not ok
        """
        try:
            result = urlfetch.fetch(url=self.status_url)
            if result.status_code // 100 != 2:
                return False, "fence status code {}, error body {}".format(result.status_code, result.content)
            else:
                return True, ""
        except Exception as e:
            return False, e.message
