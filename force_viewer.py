from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException


class CollectionReviewer:
    def __init__(self, collection, initial_auth=('user', 'pass'), hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.collection = collection
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
            self.s.driver.find_element_by_xpath('//section[@class="works-wrapper"]').screenshot(f'{output}.png')
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
            collection_url = collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        else:
            collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en&page={page}"
        self.s.driver.get(collection_url)
        print(collection_url)
        x.take_screenshot('quick_test')
        elements = self.s.driver.find_elements_by_xpath('//a[img[@class="hidden-xs file_listing_thumbnail"]]')
        data = [{"src": element.find_element_by_xpath('./img').get_attribute('src'),
                 "href": element.get_attribute('href')} for element in elements]
        for data in data:
            if data['src'] == "https://dc.utk-hyku-production.notch8.cloud/assets/work-ff055336041c3f7d310ad69109eda4a887b16ec501f35afc0a547c4adb97ee72.png":
                print(data['href'])


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
    x.review_collection()
