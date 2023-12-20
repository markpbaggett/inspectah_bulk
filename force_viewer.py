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
    """This class helps look through a collection and add viewers and thumbnails to works that are missing them.

    Args:
        collection (str): The UUID of the collection to review.
        pattern (str): The pattern to search for in the filesets to build the viewer and thumbnail from.
        initial_auth (tuple, optional): A tuple containing the username and password to get to the Hyku instance.
        hyku_instance (str, optional): The URL of the Hyku instance to use.

    """
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
        self.questionable_works = []
        self.questionable_filesets = []

    def sign_in_to_hyku(self, username, password):
        """Signs into the Hyku dashboard.

        Args:
            username (str): The username to use.
            password (str): The password to use.

        Returns:
            str: A message confirming that the user has signed in.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.sign_in_to_hyku('user', 'pass')
            Signing in to Hyku
        """
        print(f'\nSigning in to Hyku\n')
        self.s.driver.find_element_by_xpath("//input[@id='user_email']").send_keys(username, Keys.ENTER)
        self.s.driver.find_element_by_xpath("//input[@id='user_password']").send_keys(password, Keys.ENTER)
        return f'\nSigning in to Hyku\n'

    def take_screenshot(self, output):
        """Takes a screenshot of the current page.

        Args:
            output (str): The name of the file to save the screenshot to.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.take_screenshot('test')
        """
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
        """Gets the last page of the collection.

        Returns:
            int: The last page of the collection.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.get_last_page()
            1

        """
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
        """Reviews the collection and processes the works.

        Args:
            page (int, optional): The page to start on. Defaults to None.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.review_collection()
        """
        if page is None:
            print(f"Reviewing page 1 of {self.last_page}.\n")
            collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en"
        else:
            print(f"Reviewing page {page} of {self.last_page}.\n")
            collection_url = f"https://dc.utk-hyku-production.notch8.cloud/dashboard/collections/{self.collection}?utf8=%E2%9C%93&sort=score+desc%2C+system_create_dtsi+desc&per_page=100&locale=en&page={page}"
        self.s.driver.get(collection_url)
        elements = self.s.driver.find_elements_by_xpath('//a[img[@class="hidden-xs file_listing_thumbnail"]]')
        data = [{"src": element.find_element_by_xpath('./img').get_attribute('src'),
                 "href": element.get_attribute('href')} for element in elements]
        for data in data:
            if data['src'] == "https://dc.utk-hyku-production.notch8.cloud/assets/work-ff055336041c3f7d310ad69109eda4a887b16ec501f35afc0a547c4adb97ee72.png":
                self.process_work(data['href'])
        if page is None and self.last_page > 1:
            self.review_collection(page=2)
        elif page is None and self.last_page == 1:
            return
        elif page != self.last_page:
            return self.review_collection(page=page+1)
        else:
            return

    def process_work(self, url):
        """Processes a work.

        Args:
            url (str): The URL of the work to process.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.process_work('https://dc.utk-hyku-production.notch8.cloud/concern/images/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a?locale=en')

        """
        print(f"\tProcessing work {url}.")
        self.s.driver.get(url)
        self.questionable_works.append(url)
        attachments = self.s.driver.find_elements_by_xpath('//td[@class="attribute attribute-filename ensure-wrapped"]/a')
        for attachment in attachments:
            if self.pattern in attachment.text:
                self.get_attachment(attachment.get_attribute('href'))
                break
        self.edit_work(url)
        self.set_file_manager(url)
        return

    def edit_work(self, url):
        """Edits a work.

        Args:
            url (str): The URL of the work to edit.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.edit_work('https://dc.utk-hyku-production.notch8.cloud/concern/images/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a?locale=en')
        """
        edit_url = url.replace('?locale=en', '/edit?locale=en')
        self.s.driver.get(edit_url)
        save_changes_button = self.s.driver.find_element_by_xpath(
            '//input[@type="submit" and @value="Save changes" and @class="btn btn-primary"]')
        save_changes_button.click()
        return

    def set_file_manager(self, url):
        """Sets the thumbnail for a work.

        Args:
            url (str): The URL of the work to set the thumbnail for.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.set_file_manager('https://dc.utk-hyku-production.notch8.cloud/concern/images/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a?locale=en')

        """
        manager_url = url.replace('?locale=en', '/file_manager?locale=en')
        self.s.driver.get(manager_url)
        attachments = self.s.driver.find_elements_by_xpath(
            '//li/div[@class="panel panel-default"]')
        for attachment in attachments:
            attachment_title = attachment.find_element_by_xpath('./form/div/div/div[@class="form-group string required attachment_title"]/input')
            if self.pattern in attachment_title.get_attribute('value'):
                thumbnail_radio = attachment.find_element_by_xpath('./div/span/input[@name="thumbnail_id"]')
                thumbnail_radio.click()
                representative_radio = attachment.find_element_by_xpath('./div/span/input[@name="representative_id"]')
                representative_radio.click()
                self.take_screenshot(f'thumbnail_manager/{manager_url.split("/")[-2]}')
                button = self.s.driver.find_element_by_xpath('//button[@name="button" and @type="submit" and contains(@class, "btn-primary") and @data-action="save-actions"]')
                self.s.driver.execute_script("arguments[0].classList.remove('disabled')", button)
                self.s.driver.execute_script("arguments[0].click();", button)
        return

    def get_attachment(self, url):
        """Gets the attachment for a work.

        Arg:
            url (str): The URL of the attachment to get.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.get_attachment('https://dc.utk-hyku-production.notch8.cloud/concern/parent/7ab05b9f-5e10-446e-9e9f-e23e87c63c0a/attachments/e6ef4b3d-16fd-489c-ab75-827cd6bc519b')
        """
        self.s.driver.get(url)
        fileset = self.s.driver.find_elements_by_xpath('//td[@class="attribute attribute-filename ensure-wrapped"]/a')[0]
        self.edit_fileset(fileset.get_attribute('href'))
        return

    def edit_fileset(self, url):
        """Edits a fileset.

        Args:
            url (str): The URL of the fileset to edit.

        Example:
            >>> x = CollectionReviewer('f319e61e-4606-4cee-ae62-2523e63cf806', '_i', ('user', 'pass'))
            >>> x.edit_fileset('https://dc.utk-hyku-production.notch8.cloud/concern/parent/e6ef4b3d-16fd-489c-ab75-827cd6bc519b/file_sets/0e29f4c0-b1b6-42db-a480-03b80bdc4509')

        """
        fileset = url.split('/')[-1]
        self.s.driver.get(f'https://dc.utk-hyku-production.notch8.cloud/concern/file_sets/{fileset}/edit?locale=en')
        self.questionable_filesets.append(f'https://dc.utk-hyku-production.notch8.cloud/concern/file_sets/{fileset}')
        save_button = self.s.driver.find_element_by_xpath(
            '//input[@type="submit" and @value="Save" and @class="btn btn-primary"]'
        )
        save_button.click()
        return

    def log_questionable_things(self):
        with open(f'questionable_from_{self.collection}.txt', 'w') as questionable_file:
            for work in self.questionable_works:
                questionable_file.write(f'Work: {work}\n')
            for fileset in self.questionable_filesets:
                questionable_file.write(f'Fileset: {fileset}\n')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Crawl collection and add viewer.')
    parser.add_argument("-c", "--collection", dest="collection", help="Specify the collection to review.", required=True)
    parser.add_argument("-p", "--pattern", dest="pattern", help="Specify the pattern to search for.", required=True)
    args = parser.parse_args()
    settings = yaml.safe_load(open('settings.yml'))
    x = CollectionReviewer(args.collection, args.pattern, (settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    x.get_last_page()
    x.review_collection()
    x.s.driver.quit()
    x.log_questionable_things()
