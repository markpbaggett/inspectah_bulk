from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm


class CollectionReviewer:
    def __init__(self, collection, initial_auth=None, hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        self.hyku_instance = hyku_instance
        self.collection = collection
        self.bad_files = []
        if initial_auth is not None:
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )
        # self.sign_in_to_hyku(initial_auth[0], initial_auth[1])
        self.last_page = 0

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

    def review_collection(self, page=None):
        if page is not None:
            end = f"&page={page}"
        else:
            end = ""
            page = 1
        collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en{end}"
        self.s.driver.get(collection_url)
        links = [link.get_attribute('href') for link in self.s.driver.find_elements_by_xpath('//p[@class="media-heading"]/strong/a')]
        print(f"Reviewing page {page} of {self.last_page}.\n")
        for link in tqdm(links):
            work = self.review_work(link)
            if work is not None:
                self.bad_files.append(work)
        if page != self.last_page:
            return self.review_collection(page=page+1)
        else:
            return

    def write_bad_files(self):
        with open(f'{self.collection}.txt', 'w') as f:
            f.write('\n'.join(self.bad_files))
        return

    def get_last_page(self):
        collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        self.s.driver.get(collection_url)
        print(collection_url)
        last_page = [link.text for link in self.s.driver.find_elements_by_xpath("//ul//li[last()]")]
        print(last_page)
        try:
            self.last_page = int(last_page[-1])
            return int(last_page[-1])
        except ValueError:
            self.last_page = 1
            return 1

    def review_work(self, work_url):
        self.s.driver.get(work_url)
        alerts = [alert.text for alert in
                 self.s.driver.find_elements_by_xpath('//div[@class="alert alert-warning"]')]
        if len(alerts) > 0:
            return f"{work_url}: {alerts[0]}"
        return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Review works in a collection for the presence of attachments.')
    parser.add_argument("-c", "--collection", dest="collection", help="Specify the collection to review.", required=True)
    args = parser.parse_args()
    settings = yaml.safe_load(open('settings.yml'))
    x = CollectionReviewer(args.collection, (settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    x.get_last_page()
    x.review_collection()
    x.write_bad_files()