import requests
from app import app


class Responder:
    def __init__(self):
        self.patch_url_host_and_path = app.config['PATCH_URL_HOST_AND_PATH']

    def update_role(self, role_object):
        try:
            role = role_object['role_search'][0]['role'].split(' ')[0].strip()
            url = '%s/%s/update' % (self.patch_url_host_and_path, role)
            r = requests.patch(url, json=role_object)
            return r.status_code
        except Exception as e:
            print(e)
            raise e
