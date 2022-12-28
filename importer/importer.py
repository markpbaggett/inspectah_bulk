from requestium import Session, Keys
from selenium import webdriver
import yaml
import math


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

    def __determine_total_and_failures(self):
        matches  = [
            (
                paragraph.text,
                [value for value in paragraph.get_attribute('title').split(',')]
            )
            for paragraph in self.s.driver.find_elements_by_xpath('//p')
            if 'failed' in paragraph.get_attribute('title')
        ]
        results =  {
            'works': {
                'total': int(matches[0][0].split(':')[-1].strip()),
                'failed': int(matches[0][1][1].split(' ')[1])
            },
            'collections': {
                'total': int(matches[1][0].split(':')[-1].strip()),
                'failed': int(matches[1][1][1].split(' ')[1])
            },
            'filesets': {
                'total': int(matches[2][0].split(':')[-1].strip()),
                'failed': int(matches[2][1][1].split(' ')[1])
            }
        }
        return results


    def access_importer(self, importer):
        things_to_check = []
        """Access the importer"""
        self.s.driver.get(f'https://dc.utk-hyku-production.notch8.cloud/importers/{importer}?locale=en')
        """Determine the total number of attempts and how many things failed"""
        totals_and_failures = self.__determine_total_and_failures()
        """If any imports failed, add what failed and how many pages of imports the thing has."""
        for k, v in totals_and_failures.items():
            if v['failed'] > 0:
                things_to_check.append((k, math.ceil(v['total']/30)))
        results = [link.text for link in self.s.driver.find_elements_by_xpath('//tr')]
        return things_to_check

if __name__ == "__main__":
    settings = yaml.safe_load(open('settings.yml'))
    x = ImporterReviewer((settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    print(x.access_importer(91))