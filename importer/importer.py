from requestium import Session, Keys
from selenium import webdriver
import yaml
import math
from tqdm import tqdm


class ImporterReviewer:
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
            'work-entries': {
                'total': int(matches[0][0].split(':')[-1].strip()),
                'failed': int(matches[0][1][1].split(' ')[1])
            },
            'collection-entries': {
                'total': int(matches[1][0].split(':')[-1].strip()),
                'failed': int(matches[1][1][1].split(' ')[1])
            },
            'file-set-entries': {
                'total': int(matches[2][0].split(':')[-1].strip()),
                'failed': int(matches[2][1][1].split(' ')[1])
            }
        }
        return results

    def review_importer(self, importer, verbose=False):
        things_to_check = []
        all_failures = []
        """Access the importer"""
        self.s.driver.get(f'{self.hyku_instance}/importers/{importer}?locale=en')
        """Determine the total number of attempts and how many things failed"""
        totals_and_failures = self.__determine_total_and_failures()
        """If any imports failed, add what failed and how many pages of imports the thing has."""
        for k, v in totals_and_failures.items():
            if v['failed'] > 0:
                things_to_check.append((k, math.ceil(v['total']/30)))
        for thing in things_to_check:
            failures = self.process_failed_imports(importer, thing)
            for failure in failures:
                all_failures.append(failure)
        if verbose is True:
            return all_failures
        else:
            return [failure.split(' ')[0] for failure in all_failures]

    def find_source_identifiers(self, importer, source_identifiers, items=7603, verbose=False, type_to_check='work-entries'):
        self.s.driver.get(f'{self.hyku_instance}/importers/{importer}?locale=en')
        all_results = []
        total_pages = math.ceil(items / 30)
        initial_results = self.__look_at_initial_page_for_source_ids(importer, type_to_check, source_identifiers)
        all_results.extend(initial_results)
        page = 2
        with tqdm(total=total_pages - 1) as pbar:
            while page <= total_pages:
                results = self.__look_at_non_initial_page_for_source_ids(importer, type_to_check, page, source_identifiers)
                all_results.extend(results)
                page += 1
                pbar.update(1)
        return all_results

    def process_failed_imports(self, importer, type_to_check):
        all_results = []
        """Initial Route Pattern

        https://dc.utk-hyku-production.notch8.cloud/importers/91#file-set-entries
        """
        initial_results = self.__initial_process_initial_page(importer, type_to_check[0])
        for result in initial_results:
            all_results.append(result)
        page = 2
        """Subsequent Route Pattern

        https://dc.utk-hyku-production.notch8.cloud/importers/91?file_set_entries_page=2#file-set-entries
        """
        with tqdm(total=type_to_check[1] - 1) as pbar:
            while page <= type_to_check[1]:
                results = self.__process_non_initial_page(importer, type_to_check[0], page)
                for result in results:
                    all_results.append(result)
                page += 1
                pbar.update(1)
        return all_results

    def __initial_process_initial_page(self, importer, import_type):
        # print(f'{self.hyku_instance}/importers/{importer}#{import_type}')
        self.s.driver.get(f'{self.hyku_instance}/importers/{importer}#{import_type}')
        self.take_screenshot(f'screenshots/{importer}_{import_type}_initial_page')
        return [f"{link.text} PageInitial" for link in self.s.driver.find_elements_by_xpath('//tr') if 'Failed' in link.text or 'Pending' in link.text]

    def __look_at_initial_page_for_source_ids(self, importer, import_type, source_identifiers):
        self.s.driver.get(f'{self.hyku_instance}/importers/{importer}#{import_type}')
        links = [link.text for link in self.s.driver.find_elements_by_xpath('//tr')]
        found = []
        for identifier in source_identifiers:
            for link in links:
                if identifier in link:
                    self.take_screenshot(f'screenshots/source_identifier/{identifier}')
                    found.append(link)
        return found

    def __look_at_non_initial_page_for_source_ids(self, importer, import_type, page, source_identifiers):
        route_dereferencer = {
            'file-set-entries': 'file_set_entries_page',
            'collection-entries': 'collection_entries_page',
            'work-entries': 'work_entries_page'
        }
        # print(f'{self.hyku_instance}/importers/{importer}?{route_dereferencer[import_type]}={page}#{import_type}')
        self.s.driver.get(
            f'{self.hyku_instance}/importers/{importer}?{route_dereferencer[import_type]}={page}#{import_type}'
        )
        links = [link.text for link in self.s.driver.find_elements_by_xpath('//tr')]
        found = []
        for identifier in source_identifiers:
            for link in links:
                if identifier in link:
                    self.take_screenshot(f'screenshots/source_identifier/{identifier}')
                    found.append(link)
        return found

    def __process_non_initial_page(self, importer, import_type, page):
        route_dereferencer = {
            'file-set-entries': 'file_set_entries_page',
            'collection-entries': 'collection_entries_page',
            'work-entries': 'work_entries_page'
        }
        # print(f'{self.hyku_instance}/importers/{importer}?{route_dereferencer[import_type]}={page}#{import_type}')
        self.s.driver.get(
            f'{self.hyku_instance}/importers/{importer}?{route_dereferencer[import_type]}={page}#{import_type}'
        )
        self.take_screenshot(f'screenshots/{importer}_{import_type}_page_{page}')
        return [f"{link.text} Page{page}" for link in self.s.driver.find_elements_by_xpath('//tr') if 'Failed' in link.text or 'Pending' in link.text]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Find failures associated with an importer.')
    parser.add_argument("-i", "--importer", dest="importer", help="Specify csv to test.", required=True)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_argument('-t', "--type_of_crawl", dest="type_of_crawl", default="failures")
    args = parser.parse_args()
    settings = yaml.safe_load(open('settings.yml'))
    x = ImporterReviewer((settings['user'], settings['password']))
    x.sign_in_to_hyku(settings['hyku_user'], settings['hyku_password'])
    if args.type_of_crawl == 'failures':
        failures = x.review_importer(args.importer, verbose=args.verbose)
        output_file = f'failures/{args.importer}.txt'
        if args.verbose:
            output_file = f'failures/{args.importer}_verbose.txt'
        with open(output_file, 'w') as output:
            for failure in failures:
                output.write(f'{failure}\n')
    elif args.type_of_crawl == 'find_source_identifiers':
        source_identifiers = [
            'roth:4264 ',
            'roth:2468 ',
            'roth:696 ',
            'roth:4042 ',
            'roth:201 ',
            'roth:3312 ',
            'roth:7545 ',
            'roth:698 ',
            'roth:1432 ',
            'roth:6370 ',
            'roth:5187',
            'roth:4497',
            'roth:4670',
            'roth:655',
            'roth:3339',
            'roth:6370'
        ]
        identifiers = x.find_source_identifiers(args.importer, source_identifiers, verbose=args.verbose)
        output_file = f'source_identifiers/{args.importer}.txt'
        print(identifiers)
        with open(output_file, 'w') as output:
            for identifier in identifiers:
                output.write(f'{identifier}\n')
