from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import selenium



class ArchiveSpaceReviewer:
    def __init__(self, initial_auth=None, archivesspace_instance='https://archspc.lib.utk.edu/'):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver119',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.archivesspace_instance = archivesspace_instance
        self.found = []
        self.__sign_in_to_archivesspace(initial_auth[0], initial_auth[1])

    def __sign_in_to_archivesspace(self, username, password):
        print(f'\nSigning in to ArchivesSpace\n')
        self.s.driver.get(
            f'{self.archivesspace_instance}'
        )
        self.s.driver.save_screenshot('archivesspace.png')
        self.s.driver.find_element_by_xpath("//input[@id='user_username']").send_keys(username)
        self.s.driver.find_element_by_xpath("//input[@id='user_password']").send_keys(password)
        self.s.driver.find_element_by_xpath("//input[@id='login']").click()
        self.s.driver.save_screenshot('archivesspace.png')
        self.s.driver.get(
            'https://archspc.lib.utk.edu/'
        )
        self.s.driver.save_screenshot('archivesspace.png')
        return

    def search_for_resource_by_id(self, resource_id):
        # print(f'\nSearching for resource {resource_id}\n')
        self.s.driver.get(
            f'https://archspc.lib.utk.edu/search?facets%5B%5D=subjects&facets%5B%5D=publish&facets%5B%5D=level&facets%5B%5D=classification_path&facets%5B%5D=primary_type&facets%5B%5D=langcode&filter_term%5B%5D=%7B%22primary_type%22%3A%22resource%22%7D&q={resource_id}&search_field=advanced'
        )
        self.take_screenshot(f'resource_ids/{resource_id}')
        try:
            message = self.s.driver.find_element_by_xpath('/html/body/div/div[1]/div[3]/div[2]/div[2]/p')
            if message.text.strip() != "No records found":
                self.found.append(f"Scenario 1: {resource_id}: {message.text}")
        except selenium.common.exceptions.NoSuchElementException:
            try:
                matches = self.s.driver.find_element_by_xpath(f"//td[text()='{resource_id.split('.')[0].upper()}-{resource_id.split('.')[1]}']")
                if matches:
                    self.found.append(f"Scenario 2: {resource_id}")
            except selenium.common.exceptions.NoSuchElementException:
                pass
        return

    def write_found_files(self):
        with open('found.txt', 'w') as found:
            for thing in self.found:
                found.write(f"{thing}\n")
        return

    def take_screenshot(self, output):
        original_size = self.s.driver.get_window_size()
        required_width = self.s.driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = self.s.driver.execute_script('return document.body.parentNode.scrollHeight')
        self.s.driver.set_window_size(required_width, required_height)
        try:
            self.s.driver.find_element_by_xpath('/html/body/div/div[1]/div[3]/div[2]/div[2]').screenshot(f'{output}.png')
            self.s.driver.set_window_size(original_size['width'], original_size['height'])
        except selenium.common.exceptions.NoSuchElementException:
            print(f'No panel body found for {output}')
        return


if __name__ == "__main__":
    settings = yaml.safe_load(open('settings.yml'))
    x = ArchiveSpaceReviewer((settings['archivesspace_user'], settings['archivesspace_password']))
    with open('things_to_check.txt', 'r') as things:
        for thing in things:
            x.search_for_resource_by_id(thing.strip())
    x.write_found_files()