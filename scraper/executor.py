from handler.data import Queue
from scraper.scraper import Scraper
from scraper.formatter import Formatter
from urllib.parse import unquote
from app import app


class Executor:
    def __init__(self, queue_name):
        self.queue = Queue(queue_name)
        self.scraper = Scraper()
        self.formatter = Formatter()

    def get_last_item_on_queue(self):
        try:
            return self.queue.get_last()
        except Exception as e:
            raise e

    def execute_scraper(self):
        role_and_court = self.get_last_item_on_queue()[0]
        app.logger.info('scrapping {}'.format(role_and_court))
        self.remove_current_role_from_queue(role_and_court)
        try:
            return self.scraper.scrape(unquote(role_and_court.decode("utf-8")))
        except Exception as e:
            self.queue.save_failed_scrape(role_and_court)
            raise e

    def format_scrapped_data(self, data):
        return self.formatter.formatter(data)

    def remove_current_role_from_queue(self, current_role):
        try:
            self.queue.drop_successful(current_role)
            return
        except Exception as e:
            self.queue.save_failed_scrape(current_role)
            raise e

    def remove_from_queue(self, response):
        last = self.get_last_item_on_queue()[0]
        if response is 500:
            print(last)
            self.queue.save_failed_scrape(last)
            self.queue.drop_successful(last)
            return 'will retry %s', last

        self.queue.drop_successful(last)
        return '%s scrapped', last
