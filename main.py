from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from json import dump
from tqdm import tqdm


def get_and_scroll_down(driver, url):
    driver.get(url)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_all_references(driver):
    base_url = 'https://www.semanticscholar.org/'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="cited-papers"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return [urljoin(base_url, paper.get('href')) for paper in
            soup.find('div', {'id': 'cited-papers'}).find_all('a', attrs={'data-heap-id': 'citation_title'})]


def get_all_reference_titles(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="cited-papers"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return [paper.find('h3').text for paper in soup.find('div', {'id': 'cited-papers'}).find_all('a', attrs={'data-heap-id': 'citation_title'})]


def extract_authors(driver):
    try:
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                                             '//button[@data-test-id="author-list-expand" and @aria-expanded="false"]')))
        actions = ActionChains(driver)
        actions.move_to_element(button).perform()
        button.click()
    except:
        pass
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = soup.find_all('span', attrs={'data-heap-id': 'heap_author_list_item', 'data-test-id': 'author-list'})
    return [result.find('a').find('span').find('span').text for result in results if result.find('a')]


def extract_id(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//li[@data-test-id="corpus-id"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('li', attrs={'data-test-id': 'corpus-id'}).text.split(': ')[1]


def extract_title(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//h1[@data-test-id="paper-detail-title"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('h1', attrs={'data-test-id': 'paper-detail-title'}).text


def extract_abstract(driver):
    try:
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                                             '//button[@aria-label="Expand truncated text" and @data-test-id="text-truncator-toggle"]')))
        actions = ActionChains(driver)
        actions.move_to_element(button).perform()
        button.click()
    except:
        pass
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('div', attrs={'data-test-id': 'abstract-text'}).find('div').find('span').text


def extract_publication_year(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//span[@data-test-id="paper-year"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('span', attrs={'data-test-id': 'paper-year'}).find('span').find('span').text.split(' ')[-1]


def extract_citation_count(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@data-heap-nav="citing-papers"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('a', attrs={'data-heap-nav': 'citing-papers'}).find('span').text.split(' ')[0]


def extract_references_count(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@data-heap-nav="cited-papers"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find('a', attrs={'data-heap-nav': 'citing-papers'}).find('span').text.split(' ')[0]


def extract_related_papers(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@data-test-id="related-papers-list"]')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    relateds = soup.find('div', attrs={'data-test-id': 'related-papers-list'}).find_all('div',
                                                                                        attrs={'data-paper-id': True})
    return [related.find('div').find('div').find('a').find('h3').find('span').find('span').text for related in relateds]


def default_on_err(function, arg, default_value):
    try:
        return function(arg)
    except:
        return default_value


def extract(driver):
    return {
        'id': default_on_err(extract_id, driver, ''),
        'title': default_on_err(extract_title, driver, ''),
        'abstract': default_on_err(extract_abstract, driver, ''),
        'publication year': default_on_err(extract_publication_year, driver, ''),
        'authors': default_on_err(extract_authors, driver, []),
        'related papers': default_on_err(extract_related_papers, driver, ''),
        'citation count': default_on_err(extract_citation_count, driver, ''),
        'reference count': default_on_err(extract_references_count, driver, ''),
        'references': default_on_err(get_all_reference_titles, driver, '')
    }


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    professors = ['Kasaei', 'Rabiee', 'Rohban', 'Sharifi', 'Soleymani']
    for professor in professors:
        queue = deque()
        papers = []
        with open(f'{professor}.txt') as f:
            queue.extend([link.strip() for link in f.readlines()])
        for _ in tqdm(range(200)):
            if len(queue) == 0:
                break
            sleep(5)
            top = queue.popleft()
            try:
                get_and_scroll_down(driver, top)
                references = default_on_err(get_all_references, driver, [])
                queue.extend(references)
                papers.append(extract(driver))
            except:
                pass
        dump(papers, open(f'crawled_paper_{professor}.txt', 'w'))


if __name__ == '__main__':
    main()
