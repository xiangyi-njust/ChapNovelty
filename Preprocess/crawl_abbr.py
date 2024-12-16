import threading
import json
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def crawl_url(url, driver):
    try:
        driver.get(url)
        try:
            element = WebDriverWait(driver, 10).until(
                lambda driver: driver.find_element(By.CSS_SELECTOR, "div.rprt") or
                               driver.find_element(By.CSS_SELECTOR, "div[rprt abstract]")
            )
        finally:
            title_elems = driver.find_elements(By.CSS_SELECTOR, "p.title")
            attr_elems = driver.find_elements(By.CSS_SELECTOR, "div.nlmcat_aux")

            if len(title_elems) == 0:
                title_elem = driver.find_element_by_css_selector("h1.title")
                title = title_elem.text
                attr_elems = driver.find_elements_by_css_selector("div.nlmcat_entry dt")
                attr_value = driver.find_elements_by_css_selector("div.nlmcat_entry dd")
                attr_texts = [elem.text for elem in attr_elems]
                value_texts = [elem.text for elem in attr_value]
                pos = attr_texts.index("NLM Title Abbreviation:")
                value = value_texts[pos]

                url_to_content[url] = {
                    'title': title,
                    'attri': value
                }
            else:
                titles = [title.text for title in title_elems]
                values = [elem.text for elem in attr_elems]
                url_to_content[url] = {
                    'title': titles,
                    'attri': values
                }
    except Exception as e:
        print(f"{e}")


def call_parse(links, part_name):
    for link in tqdm(links, desc=part_name):
        crawl_url(link)


def split_filenames(urls, k):
    file_parts = {}
    part_length = int(len(urls) / k)
    for i in range(k + 1):
        part_name = 'part_{}'.format(i)
        if (i + 1) * part_length > len(urls):
            part_files = urls[i * part_length:]
        else:
            part_files = urls[i * part_length:(i + 1) * part_length]
        file_parts[part_name] = part_files

    return file_parts


def process_in_threads(url_dicts):
    threads = []

    for part_name in url_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(url_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    df = pd.read_csv("data/nlm/standard_journals_nlm_url_part_3.csv")
    urls = df['URL'].tolist()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(executable_path="E:\Config\Webdriver\chromedriver-win64\chromedriver.exe",
                              options=chrome_options)

    url_to_content = {}
    for url in tqdm(urls):
        crawl_url(url, driver)
    driver.quit()
    json_content = json.dumps(url_to_content, indent=4)
    with open("data/nlm/part_3_results.json", 'w') as f:
        f.write(json_content)
