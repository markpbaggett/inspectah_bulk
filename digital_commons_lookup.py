from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


class ETDReview:
    def __init__(self, filename, initial_auth=('user', 'pass')):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver120',
            browser='chrome',
            default_timeout=15,
        )
        self.file = filename
        self.results = []
        self.sign_in(initial_auth)
        self.review_pages()


    def sign_in(self, auth):
        self.s.driver.get(
            'https://trace.tennessee.edu/cgi/editor.cgi?article=9500&window=event_history&context=utk_graddiss'
        )
        self.s.driver.find_element_by_xpath("//input[@id='auth_email']").send_keys(auth[0])
        self.s.driver.find_element_by_xpath("//input[@id='auth_password']").send_keys(auth[1])
        submit = self.s.driver.find_element_by_xpath("//button[@name='submit']")
        time.sleep(40)
        submit.click()
        return

    def review(self, page):
        self.s.driver.get(
            page
        )
        self.s.driver.find_element_by_xpath('//form/table/tbody').screenshot(f'etds/{page.split("=")[1]}.png')
        rows = self.s.driver.find_elements_by_xpath("//form/table/tbody/tr")
        result = False
        for row in rows:
            x = row.find_elements_by_xpath(".//td")
            if len(x) == 5 and x[1].text == 'Accepted' and x[2].text == 'Graduate School':
                result = True
                break
        if result is False:
            self.results.append(page)
        return

    def review_pages(self):
        with open(self.file, 'r') as f:
            for line in tqdm(f.readlines()):
                self.review(line.strip())
        with open('output_diss.csv', 'w') as new_f:
            for result in self.results:
                new_f.write(result + '\n')


if __name__ == "__main__":
    x = ETDReview('pages.txt', ('email', 'password'))