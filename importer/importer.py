from requestium import Session, Keys
from selenium import webdriver
import yaml


class ImporterReviewer:
    def __init__(self, initial_auth=None, hyku_instance='https://dc.utk-hyku-production.notch8.cloud'):
        self.s = Session(
            webdriver_path='/usr/local/bin/chromedriver',
            browser='chrome',
            default_timeout=15,
            webdriver_options={'arguments': ['headless']}
        )
        if initial_auth is not None:
            self.s.driver.get(
                f'https://{initial_auth[0]}:{initial_auth[1]}@{hyku_instance.replace("https://", "")}/users/sign_in?locale=en'
            )

    def sign_in_to_hyku(self, username, password):
        self.s.driver.find_element_by_xpath("//input[@id='user_email']").send_keys(username, Keys.ENTER)
        self.s.driver.find_element_by_xpath("//input[@id='user_password']").send_keys(password, Keys.ENTER)
        return

    def take_screenshot(self, output):
        return self.s.driver.save_screenshot(f'{output}.png')

    def access_importer(self, importer):
        errors = []
        self.s.driver.get(f'https://dc.utk-hyku-production.notch8.cloud/importers/{importer}?locale=en')
        results = [link.text for link in self.s.driver.find_elements_by_xpath('//tr')]
        pagination = [link.get_attribute('href') for link in self.s.driver.find_elements_by_xpath('//ul[@class="pagination"]/li/a')]
        return pagination

if __name__ == "__main__":
    settings = yaml.safe_load(open('settings.yml'))
    x = ImporterReviewer((settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    print(x.access_importer(25))