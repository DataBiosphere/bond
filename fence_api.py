from google.appengine.api import urlfetch
import endpoints


class FenceApi:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_credentials_google(self, access_token):
        """
        Calls fence POST /user/credentials/google api
        :param access_token: oauth access token
        :return: service account key json
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = urlfetch.fetch(url=self.base_url + '/user/credentials/google', headers=headers, method=urlfetch.POST)
        if result.status_code == 200:
            return result.content
        else:
            raise endpoints.InternalServerErrorException("fence status code {}, error body {}".format(result.status_code, result.content))