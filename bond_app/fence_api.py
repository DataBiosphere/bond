from werkzeug import exceptions
import requests
import logging


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
        result = requests.post(url=self.credentials_google_url, headers=headers)
        # Logging the `result.content` here as part of debugging/troubleshooting for:
        # https://broadworkbench.atlassian.net/browse/CA-1109
        # Logging of the `response.content` can probably be removed after we have resolved this issue
        logging.info("Getting new Service Account JSON Key from Fence via - request: POST {} - status code: {} - body: {}" \
                     .format(self.credentials_google_url, result.status_code, result.content))
        if result.status_code // 100 == 2:
            return result.content
        else:
            raise exceptions.InternalServerError("fence status code {}, error body {}".format(result.status_code,
                                                                                              result.content))

    def delete_credentials_google(self, access_token, key_id):
        """
        Calls fence DELETE /user/credentials/google/key_id api
        :param access_token: oauth access token
        :param key_id: key_id to delete
        :return: service account key json
        """
        headers = {'Authorization': 'Bearer ' + access_token}
        result = requests.delete(url=self.delete_service_account_url + key_id, headers=headers)
        logging.info("request: DELETE {} - status code: {}".format(self.delete_service_account_url, result.status_code))
        # Sometimes Fence returns a 4xx error like when it cannot find the key_id that we are trying to delete. From
        # our perspective, that's fine, we wanted to delete that key anyways, so if Fence has already deleted it and no
        # longer knows about it, then our work is done. Rather than disrupt the unlinking process, we tolerate the 4xx
        if result.status_code // 100 != 2 and result.status_code // 100 != 4:
            raise exceptions.InternalServerError("fence status code {}, error body {}".format(result.status_code, result.content))

    def revoke_refresh_token(self, refresh_token):
        result = requests.post(url=self.revoke_url, data=refresh_token)
        if result.status_code // 100 != 2:
            if result.status_code != 400:
                raise exceptions.InternalServerError("fence status code {}, error body {}"
                                                     .format(result.status_code, result.content))

    def status(self):
        """
        Tests the connection to fence
        :return: 2 values: boolean ok or not, status message if not ok
        """
        try:
            result = requests.get(url=self.status_url)
            if result.status_code // 100 != 2:
                return False, "fence status code {}, error body {}".format(result.status_code, result.content)
            else:
                return True, ""
        except Exception as e:
            return False, str(e)
