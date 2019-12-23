from handler.db import Redis


class Queue:
    def __init__(self):
        self.redis = Redis()

    def queue_roles(self, roles):
        return self.redis.save_multiple(roles)

    def add_one_to_queue(self, roles):
        return self.redis.save(roles)

    def get_last(self):
        return self.redis.get_last()

    def drop_successful(self, role):
        return self.redis.delete(role)

    def drop_successful_retry(self, role):
        return self.redis.delete_exception(role)

    def save_failed_scrape(self, role):
        return self.redis.save_exception(role)

    def get_list_length(self, list_name):
        return self.redis.get_list_length(list_name)
