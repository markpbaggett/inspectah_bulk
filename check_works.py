from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm


class CollectionReviewer:
    def __init__(self, initial_auth=None, hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.hyku_instance = hyku_instance
        if initial_auth is not None:
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )

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
        self.s.driver.find_element_by_xpath('//div[@class="panel-body"]').screenshot(f'{output}.png')
        self.s.driver.set_window_size(original_size['width'], original_size['height'])
        return

    def review_collection(self, collection="1178a839-2a9f-468e-9d2e-a5116d39edf5"):
        things_to_check = []
        """Access the importer"""
        collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        self.s.driver.get(collection_url)
        links = [link.get_attribute('href') for link in self.s.driver.find_elements_by_xpath('//p[@class="media-heading"]/strong/a')]
        for link in tqdm(links):
            work = self.review_work(link)
            if work is not None:
                things_to_check.append(work)
        with open(f'{collection}.txt', 'w') as f:
            f.write('\n'.join(things_to_check))
        return

    def review_work(self, work_url):
        self.s.driver.get(work_url)
        alerts = [alert.text for alert in
                 self.s.driver.find_elements_by_xpath('//div[@class="alert alert-warning"]')]
        if len(alerts) > 0:
            return f"{work_url}: {alerts[0]}"
        return

if __name__ == "__main__":
     settings = yaml.safe_load(open('settings.yml'))
     x = CollectionReviewer((settings['user'], settings['password']))
     x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
     x.review_collection('7b5bbf91-cac0-4360-88ac-2011f74d1cfe')
