from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm
import os
import random

class CollectionReviewer:
    def __init__(self, initial_auth=None, hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver116',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.hyku_instance = hyku_instance
        if initial_auth is not None:
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )
        # self.sign_in_to_hyku(initial_auth[0], initial_auth[1])

    def sign_in_to_hyku(self, username, password):
        print(f'\nSigning in to Hyku\n')
        self.s.driver.find_element_by_xpath("//input[@id='user_email']").send_keys(username, Keys.ENTER)
        self.s.driver.find_element_by_xpath("//input[@id='user_password']").send_keys(password, Keys.ENTER)
        return

    def take_screenshot(self, output):
        original_size = self.s.driver.get_window_size()
        required_width = self.s.driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = self.s.driver.execute_script('return document.body.parentNode.scrollHeight')
        self.s.driver.set_window_size(required_width, required_height)
        try:
            self.s.driver.find_element_by_xpath('//div[@class="panel-body"]').screenshot(f'{output}.png')
            self.s.driver.set_window_size(original_size['width'], original_size['height'])
        except selenium.common.exceptions.NoSuchElementException:
            print(f'No panel body found for {output}')
        return

    def take_work_screenshot(self, output):
        original_size = self.s.driver.get_window_size()
        required_width = self.s.driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = self.s.driver.execute_script('return document.body.parentNode.scrollHeight')
        self.s.driver.set_window_size(required_width, required_height)
        try:
            self.s.driver.find_element_by_xpath('//div[@class="work-type-container"]').screenshot(f'{output}.png')
            self.s.driver.set_window_size(original_size['width'], original_size['height'])
        except selenium.common.exceptions.NoSuchElementException:
            print(f'No work type container found for {output}')
        return

    def access_collection_page(self):
        self.s.driver.get('https://dc.utk-hyku-production.notch8.cloud/dashboard/collections?utf8=%E2%9C%93&per_page=100&locale=en')
        links = [{"link": link.get_attribute('href'), "text": link.text} for link in
                 self.s.driver.find_elements_by_xpath('//div[@class="thumbnail-title-wrapper"]/a[not(@title)]')]
        for link in links:
            if '\n' in  link['text']:
                link['text'] = link['text'].split('\n')[1]
            else:
                link['text'] = link['text'].split('Display summary details of ')[1]
        print('\nReviewing Collections\n')
        for link in tqdm(links):
            self.review_collection(link)
        return

    def review_collection(self, collection):
        collection_metadata = {
            "title": collection['text'],
            "link": f"{collection['link']}&per_page=20&sort=score+desc%2C+system_create_dtsi+desc",
            "directory": f"{collection['text'].replace(' ', '_').replace('/', '').strip()}",
            "works": 0,
        }
        if 'Default Admin Set' not in collection_metadata['title']:
            self.s.driver.get(collection_metadata['link'])
            works = [link.text for link in self.s.driver.find_elements_by_xpath('//dl[@class="dl-horizontal metadata-collections"]/dd/span[@itemprop="total_items"]')]
            if len(works) == 1:
                collection_metadata['works'] = int(works[0])
            collection_metadata['last_page'] = [link.text for link in self.s.driver.find_elements_by_xpath('//ul[@class="pagination"]/li/a')][-1]
            collection_metadata['middle_page'] = math.ceil(int(collection_metadata['last_page'].replace(',', ''))/2)
            print(collection_metadata)
            ### Create directory for collection and Take Screenshots of Initial Page
            if not os.path.exists(f"collection_review_2/{collection_metadata['directory']}"):
                os.makedirs(f"collection_review_2/{collection_metadata['directory']}")
                os.makedirs(f"collection_review_2/{collection_metadata['directory']}/screenshots")
            self.take_screenshot(f"collection_review_2/{collection_metadata['directory']}/screenshots/initial_page")
            check_these = [link.get_attribute('href') for link in self.s.driver.find_elements_by_xpath('//div[@class="media"]/a[@class="media-left"]')]
            self.check_some_works(check_these, collection_metadata['directory'])
            ### Take Screenshots of Middle Page
            self.s.driver.get(f"{collection_metadata['link']}&page={collection_metadata['middle_page']}")
            self.take_screenshot(f"collection_review_2/{collection_metadata['directory']}/screenshots/middle_page")
            check_these = [link.get_attribute('href') for link in
                           self.s.driver.find_elements_by_xpath('//div[@class="media"]/a[@class="media-left"]')]
            self.check_some_works(check_these, collection_metadata['directory'])
            ### Take Screenshots of Last Page
            self.s.driver.get(f"{collection_metadata['link']}&page={collection_metadata['last_page']}")
            self.take_screenshot(f"collection_review_2/{collection_metadata['directory']}/screenshots/last_page")
            check_these = [link.get_attribute('href') for link in
                           self.s.driver.find_elements_by_xpath('//div[@class="media"]/a[@class="media-left"]')]
            self.check_some_works(check_these, collection_metadata['directory'])
        return

    def review_work(self, work, output_directory):
        self.s.driver.get(work)
        self.take_work_screenshot(f"collection_review_2/{output_directory}/screenshots/{work.split('/')[-1].replace('?locale=en', '')}")
        return

    def check_some_works(self, works, output_directory):
        if len(works) > 2:
            works = random.sample(works, 3)
        for work in works:
            self.review_work(work, output_directory)
        return



if __name__ == "__main__":
    settings = yaml.safe_load(open('settings.yml'))
    x = CollectionReviewer((settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    x.access_collection_page()
    # sample_collection = {'link': 'https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/afc86f32-3367-4a89-93f5-9eeaea24cf38?locale=en', 'text': 'WPA/TVA Archaeology Photographs'}
    # x.review_collection(sample_collection)
    # x.review_work('https://dc.utk-hyku-production.notch8.cloud/concern/images/f4028afb-96c3-4b1b-8c9e-173b8f98a140?locale=en', 'WPATVA_Archaeology_Photographs')