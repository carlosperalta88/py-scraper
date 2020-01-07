from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC


def get_cells_of_rows(rows):
    rows_data = []
    for row in rows:
        row_data = []
        cols = row.find_elements(By.TAG_NAME, 'td')
        for col in cols:
            row_data.append(col.text)
        rows_data.append(row_data)
    return rows_data


def get_details_url(text):
    return text.split("'")[1]


def validate_rows_existence(tbody):
    return (lambda x: x.find_elements_by_tag_name('tr') if len(
            x.text) > 0 else [])(tbody)


def split_role_and_court(role_and_court):
    return role_and_court.split('*')


def split_role_in_components(role):
    return role.split('-')


class Scraper:
    def __init__(self):
        self.options = Options()
        self.options.headless = True
        self.driver = webdriver.Chrome(executable_path='chromedriver', chrome_options=self.options)
        self.wait = WebDriverWait(self.driver, 15)
        self.known_exceptions = (NoSuchElementException, StaleElementReferenceException)

    def connect(self, url):
        try:
            return self.driver.get(url)
        except Exception as err:
            print(err)
            self.driver.close()
            return None

    def switch_context(self, xpath):
        try:
            return self.driver.switch_to.frame(self.driver.find_element_by_xpath(xpath))
        except Exception as err:
            print(err)
            self.driver.close()
            return None

    def search_cause(self, role_and_court):
        try:
            court_name = split_role_and_court(role_and_court)[1]
            cause_id = split_role_in_components(split_role_and_court(role_and_court)[0])[1]
            cause_year = split_role_in_components(split_role_and_court(role_and_court)[0])[2]
            cause = self.driver.find_element_by_xpath('.//*[@id="RUC"]/input[1]')
            cause.clear()
            cause.send_keys(cause_id)
            year = self.driver.find_element_by_name('ERA_Causa')
            year.clear()
            year.send_keys(cause_year)
            court = Select(self.driver.find_element_by_name('COD_Tribunal'))
            court.select_by_visible_text(court_name)
            query_button = self.driver.find_element_by_xpath('.//html/body/form/table[6]/tbody/tr/td[2]/a[1]')
            query_button.click()
        except Exception as err:
            print(err)
            raise err

    def scrape(self, role_and_court):
        data = {}
        try:
            self.connect('https://civil.pjud.cl/CIVILPORWEB/')
            self.switch_context('/html/frameset/frameset/frame[2]')
            self.search_cause(role_and_court)
            self.wait.until(EC.presence_of_element_located((By.XPATH, './/*[@id="contentCellsAddTabla"]/tbody/tr')))
            causes_container = self.driver.find_element_by_xpath('.//*[@id="contentCellsAddTabla"]/tbody')
            causes = causes_container.find_elements_by_tag_name('tr')
            data['role_search'] = get_cells_of_rows(causes)
            causes[0].find_element_by_tag_name('a').click()

            self.wait.until(EC.presence_of_element_located((By.XPATH, './html/body/form/table[3]/tbody/tr[2]/td[1]')))
            status = self.driver.find_element_by_xpath('./html/body/form/table[3]/tbody/tr[2]/td[1]')
            data['status'] = status.text

            receptor_button = self.driver.find_element_by_xpath('./html/body/form/table[5]/tbody/tr/td[2]/img')
            receptor_button.click()

            self.wait.until(EC.presence_of_element_located((By.XPATH, './/*[@id="ReceptorDIV"]/table[4]/tbody')))
            receptor_data = validate_rows_existence(self.driver.find_element_by_xpath('.//*[@id="ReceptorDIV"]/table[4]/tbody'))
            data['receptor'] = get_cells_of_rows(receptor_data) if len(receptor_data) > 0 else []

            close_receptor_popup = self.driver.find_element_by_xpath('/html/body/form/div[2]/table[5]/tbody/tr/td/a')
            close_receptor_popup.click()

            self.driver.switch_to.default_content()
            self.switch_context('/html/frameset/frameset/frame[2]')

            books = Select(self.driver.find_element_by_name('CRR_Cuaderno'))
            book_options = books.options
            book_length = len(book_options)
            book_count = 0
            data['cause_history'] = []
            for book in book_options:
                book_count += 1

                history_by_book = {'book': book_options[book_count-1].text, 'history': None}

                self.driver.switch_to.default_content()
                self.switch_context('/html/frameset/frameset/frame[2]')

                sleep(2)
                requested_stories = self.driver.find_elements_by_xpath(
                    './html/body/form/table[7]/tbody/tr[2]/td/table/tbody/tr/td/div/div[1]/table[2]/tbody/tr')

                history_by_book['history'] = get_cells_of_rows(requested_stories)
                data['cause_history'].append(history_by_book)

                if book_count < book_length:
                    books.select_by_visible_text(book_options[book_count].text)
                    self.driver.find_element_by_xpath('.//*[@id="botoncuaderno"]').click()
                    self.driver.switch_to.default_content()
                    self.switch_context('/html/frameset/frameset/frame[2]')
                    books = Select(self.driver.find_element_by_name('CRR_Cuaderno'))
                    book_options = books.options

            pending_docs = self.driver.find_element_by_xpath('/html/body/form/table[7]/tbody/tr[1]/td[7]')
            self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/form/table[7]/tbody/tr[1]/td[7]')))
            pending_docs.click()

            exh = self.driver.find_element_by_xpath('/html/body/form/table[7]/tbody/tr[1]/td[9]')
            self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/form/table[7]/tbody/tr[1]/td[9]')))
            exh.click()

            pending_docs_container = self.driver.find_element_by_xpath(
                './html/body/form/table[7]/tbody/tr[2]/td/table/tbody/tr/td/div/div[4]/table[2]/tbody')
            data['pending_docs'] = get_cells_of_rows((lambda x: x.find_elements_by_tag_name('tr') if len(
                x.text) > 0 else [])(pending_docs_container))

            exh_container = self.driver.find_element_by_xpath(
                './html/body/form/table[7]/tbody/tr[2]/td/table/tbody/tr/td/div/div[5]/table[2]/tbody')
            data['exhort'] = get_cells_of_rows((lambda x: x.find_elements_by_tag_name('tr') if len(
                x.text) > 0 else [])(exh_container))

            exh_rows = (lambda x: x.find_elements_by_tag_name('tr') if len(
                x.text) > 0 else [])(exh_container)

            exhorts_links = []
            data['exhorts'] = []
            for row in exh_rows:
                a = row.find_element_by_tag_name('a')
                link = get_details_url(a.get_attribute('onclick'))
                name = a.text
                exhorts_links.append([name, link])

            for link in exhorts_links:
                self.connect('https://civil.pjud.cl{}'.format(link[1]))
                self.wait.until(EC.presence_of_element_located((By.XPATH, './html/body/form/table[3]/tbody/tr[3]/td/div/table/tbody')))

                exh_popup_rows = self.driver.find_elements_by_xpath('/html/body/form/table[3]/tbody/tr[3]/td/div/table/tbody/tr')
                del exh_popup_rows[-1]
                data['exhorts'].append([link[0], get_cells_of_rows(exh_popup_rows)])

            self.driver.close()
            # print(data)
            return data
        except Exception as err:
            self.driver.close()
            raise err
