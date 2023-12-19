from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class CollectionReviewer:
    def __init__(self, collection, pattern, initial_auth=('user', 'pass'), hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.collection = collection
        self.pattern = pattern
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver120',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.hyku_instance = hyku_instance
        if initial_auth is not None:
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )
        self.last_page = 1

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
            # self.s.driver.find_element_by_xpath('//section[@class="works-wrapper"]').screenshot(f'{output}.png')
            self.s.driver.find_element_by_xpath('//div[@class="main-content maximized"]').screenshot(f'{output}.png')
            self.s.driver.set_window_size(original_size['width'], original_size['height'])
        except NoSuchElementException:
            print(f'No works wrapper found for {output}')
        return

    def get_last_page(self):
        collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        self.s.driver.get(collection_url)
        last_page = [link.text for link in self.s.driver.find_elements_by_xpath("//ul//li[last()]")]
        try:
            self.last_page = int(last_page[-1])
            return int(last_page[-1])
        except ValueError:
            self.last_page = 1
            return 1

    def review_collection(self, page=None):
        if page is None:
            collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        else:
            collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en&page={page}"
        self.s.driver.get(collection_url)
        elements = self.s.driver.find_elements_by_xpath('//a[img[@class="hidden-xs file_listing_thumbnail"]]')
        data = [{"src": element.find_element_by_xpath('./img').get_attribute('src'),
                 "href": element.get_attribute('href')} for element in elements]
        for data in data:
            if data['src'] == "https://dc.utk-hyku-production.notch8.cloud/assets/work-ff055336041c3f7d310ad69109eda4a887b16ec501f35afc0a547c4adb97ee72.png":
                print(data['href'])

    def process_work(self, url):
        self.s.driver.get(url)
        attachments = self.s.driver.find_elements_by_xpath('//td[@class="attribute attribute-filename ensure-wrapped"]/a')
        for attachment in attachments:
            if self.pattern in attachment.text:
                self.get_attachment(attachment.get_attribute('href'))
        self.edit_work(url)
        self.set_file_manager(url)
        return

    def edit_work(self, url):
        edit_url = url.replace('?locale=en', '/edit?locale=en')
        self.s.driver.get(edit_url)
        save_changes_button = self.s.driver.find_element_by_xpath(
            '//input[@type="submit" and @value="Save changes" and @class="btn btn-primary"]')
        save_changes_button.click()
        return

    def set_file_manager(self, url):
        manager_url = url.replace('?locale=en', '/file_manager?locale=en')
        self.s.driver.get(manager_url)
        attachments = self.s.driver.find_elements_by_xpath(
            '//li/div[@class="panel panel-default"]')
        for attachment in attachments:
            attachment_title = attachment.find_element_by_xpath('./form/div/div/div[@class="form-group string required attachment_title"]/input')
            if self.pattern in attachment_title.get_attribute('value'):
                thumbnail_radio = attachment.find_element_by_xpath('//input[@name="thumbnail_id"]')
                thumbnail_radio.click()
                representative_radio = attachment.find_element_by_xpath('//input[@name="representative_id"]')
                representative_radio.click()
                button = self.s.driver.find_element_by_xpath('//button[@name="button" and @type="submit" and contains(@class, "btn-primary") and @data-action="save-actions"]')
                self.s.driver.execute_script("arguments[0].classList.remove('disabled')", button)
                self.take_screenshot('file_manager')
                self.s.driver.execute_script("arguments[0].click();", button)
        return

    def get_attachment(self, url):
        self.s.driver.get(url)
        fileset = self.s.driver.find_elements_by_xpath('//td[@class="attribute attribute-filename ensure-wrapped"]/a')[0]
        self.edit_fileset(fileset.get_attribute('href'))
        return

    def edit_fileset(self, url):
        fileset = url.split('/')[-1]
        self.s.driver.get(f'https://dc.utk-hyku-production.notch8.cloud/concern/file_sets/{fileset}/edit?locale=en')
        save_button = self.s.driver.find_element_by_xpath(
            '//input[@type="submit" and @value="Save" and @class="btn btn-primary"]')
        save_button.click()
        return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Crawl collection and add viewer.')
    parser.add_argument("-c", "--collection", dest="collection", help="Specify the collection to review.", required=True)
    args = parser.parse_args()
    settings = yaml.safe_load(open('settings.yml'))
    # collection_for_testing = 'f319e61e-4606-4cee-ae62-2523e63cf806'
    x = CollectionReviewer(args.collection, (settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    x.get_last_page()
    # x.review_collection()
    # x.process_work('https://dc.utk-hyku-production.notch8.cloud/concern/images/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a?locale=en', '_i')
    # print(x.get_attachment('https://dc.utk-hyku-production.notch8.cloud/concern/parent/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a/attachments/e6ef4b3d-16fd-489c-ab75-827cd6bc519b'))
    # print(x.edit_fileset('https://dc.utk-hyku-production.notch8.cloud/concern/parent/e6ef4b3d-16fd-489c-ab75-827cd6bc519b/file_sets/0e29f4c0-b1b6-42db-a480-03b80bdc4509'))
    # x.edit_work('https://dc.utk-hyku-production.notch8.cloud/concern/images/721079f9-d11f-4f8f-a88c-8c63ed9d2dd0/edit?locale=en')
    x.set_file_manager('https://dc.utk-hyku-production.notch8.cloud/concern/images/721079f9-d11f-4f8f-a88c-8c63ed9d2dd0?locale=en')

