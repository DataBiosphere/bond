from google.appengine.api import urlfetch
import endpoints


class FenceApi:
    def __init__(self, credentials_google_url, revoke_url):
        self.credentials_google_url = credentials_google_url
        self.revoke_url = revoke_url

    def get_credentials_google(self, access_token):
        """
        Calls fence POST /user/credentials/google api
        :param access_token: oauth access token
        :return: service account key json
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = urlfetch.fetch(url=self.credentials_google_url, headers=headers, method=urlfetch.POST)
        if result.status_code == 200:
            return result.content
        else:
            raise endpoints.InternalServerErrorException("fence status code {}, error body {}".format(result.status_code, result.content))

    def revoke_refresh_token(self, refresh_token):
        result = urlfetch.fetch(url=self.revoke_url, method=urlfetch.POST, payload=refresh_token)
        if result.status_code == 200:
            return
        else:
            raise endpoints.InternalServerErrorException("fence status code {}, error body {}".format(result.status_code, result.content))
