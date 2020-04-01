import requests
import logging
from app import app


class Responder:
    def __init__(self):
        self.post_url_host_and_path = app.config['POST_URL_HOST_AND_PATH']

    def update_role(self, role_object):
        try:
            logging.warning(role_object['role_search'][0]['role'])
            role = role_object['role_search'][0]['role'].split(' ')[0].strip()
            url = '%s/add/%s' % (self.post_url_host_and_path, role)
            r = requests.post(url, json=role_object)
            return r.status_code
        except Exception as e:
            logging.info('responder')
            logging.error(e)
            raise e
