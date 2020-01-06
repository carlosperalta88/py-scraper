import redis


class Redis:
    def __init__(self, list_name):
        self.port = 6379
        self.db = 1
        self.r = redis.Redis(host='localhost', port=self.port, db=self.db)
        self.list_name = list_name
        self.exception_list_name = 'failed_roles'

    def save(self, role):
        try:
            self.r.lpush(self.list_name, role)
            return 201
        except Exception as err:
            raise err

    def save_exception(self, role):
        try:
            self.r.lpush(self.exception_list_name, role)
            return 201
        except Exception as err:
            raise err

    def get_list_length(self, list_name):
        try:
            list_length = self.r.llen(list_name)
            return list_length
        except Exception as err:
            raise err

    def save_multiple(self, roles):
        try:
            self.r.lpush(self.list_name, *roles)
            return 201
        except Exception as err:
            raise err

    def get_last(self):
        try:
            return self.r.lrange(self.list_name, -1, -1)
        except Exception as err:
            raise err

    def delete(self, role):
        try:
            self.r.lrem(self.list_name, -1, role)
            return 200
        except Exception as err:
            raise err
