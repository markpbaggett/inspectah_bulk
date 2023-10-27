from requestium import Session, Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
import yaml
import math
from tqdm import tqdm
import os
import random
import time
import csv


class CollectionReviewer:
    def __init__(self, works_csv, failed_csv, initial_auth=None, hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.works = self.__find_works(works_csv)
        self.failures = self.__find_failed(failed_csv)
        self.instance = hyku_instance
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver118',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.hyku_instance = hyku_instance
        if initial_auth is not None:
            print(hyku_instance)
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )

    def sign_in_to_hyku(self, username, password):
        print(f'\nSigning in to Hyku\n')
        self.s.driver.find_element_by_xpath("//input[@id='user_email']").send_keys(username, Keys.ENTER)
        self.s.driver.find_element_by_xpath("//input[@id='user_password']").send_keys(password, Keys.ENTER)
        return

    def take_work_screenshot(self, output):
        original_size = self.s.driver.get_window_size()
        required_width = self.s.driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = self.s.driver.execute_script('return document.body.parentNode.scrollHeight')
        self.s.driver.set_window_size(required_width, required_height)
        try:
            self.s.driver.find_element_by_xpath('//div[@class="main-content"]').screenshot(f'{output}.png')
            self.s.driver.set_window_size(original_size['width'], original_size['height'])
        except selenium.common.exceptions.NoSuchElementException:
            print(f'No work type container found for {output}')
        return

    def upload_file(self, file_set_uuid):
        # https://dc.utk-hyku-production.notch8.cloud/concern/file_sets/03b2d643-9d2e-4114-a843-e829143fd114/edit?locale=en#versioning_display
        self.s.driver.get('https://dc.utk-hyku-production.notch8.cloud/concern/file_sets/abf76cc6-e841-4aca-b38c-8a8c025b3a64/edit?locale=en#versioning_display')
        file_input = self.s.driver.find_element(By.XPATH, "//input[@id='file_set_files']")
        file_input.send_keys('/Users/markbaggett/tmp/wwiioh:2171.xml')
        time.sleep(2)
        button_element = self.s.driver.find_element(By.NAME, 'update_versioning')
        button_element.click()
        self.take_work_screenshot('screenshots/0')
        return

    @staticmethod
    def __find_works(the_csv):
        output = []
        with open(the_csv, 'r') as my_csv:
            csv_reader = csv.DictReader(my_csv)
            for row in csv_reader:
                if row['model'] != 'Collection':
                    output.append({'id': row['id'], 'source_id': row['source_identifier'], 'model': row['model']})
        return output

    @staticmethod
    def __find_failed(failed_csv):
        failures = []
        with open(failed_csv, 'r') as my_csv:
            csv_reader = csv.DictReader(my_csv)
            for row in csv_reader:
                failures.append({'id': row['source_identifier'], 'title': row['title']})
        return failures

    def process_failures(self):
        found = []
        for failure in self.failures:
            pid = failure['id'].split('_')[0]
            result = next(filter(lambda item: item['source_id'] == pid, self.works), None)
            if result is not None:
                path_to_parent = f"{self.instance}/concern/{result['model'].lower()}s/{result['id']}"
                found.append({'parent': path_to_parent, 'title': failure['title'], 'id': failure['id']})
            else:
                print(f"Could not find {pid} in the works csv.")
        return

if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description='Review a collection.')
    # parser.add_argument("-u", "--username", dest="username", help="Specify the username.", required=True)
    # parser.add_argument("-p", "--password", dest="password", help="Specify the password.", required=True)
    # args = parser.parse_args()
    settings = yaml.safe_load(open('settings.yml'))
    works_csv = '/Users/markbaggett//Downloads/export_340_from_importer_1.csv'
    failed_csv = '/Users/markbaggett/PycharmProjects/exodus/collections/wwiioh/errors/import_341_20230926170908_511_errored_entries.csv'
    x = CollectionReviewer(works_csv, failed_csv, (settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    x.process_failures()
    # x.upload_file()