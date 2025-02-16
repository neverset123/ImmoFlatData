from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import json
from datetime import datetime
import pandas as pd
import re
from config import configs
import logging
import os
import requests
import time
# from seleniumbase import SB
from seleniumbase import Driver
from bs4 import BeautifulSoup
# from selenium_recaptcha_solver import RecaptchaSolver
# from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def cal_stats(df: pd.DataFrame, config: dict):
    for col, formula in config.stat_cols.items():
        if col in df.columns:
            df[col] = eval(formula)
        else:
            logging.info(f"skip {col} stat")
    return df

def captcha_check(html: str, driver: webdriver.Chrome):
    # solver = RecaptchaSolver(driver=driver)
    chaptcha_part = html.split(r"</title>")[0].split(r"<title>")[1]
    if "Ich bin kein Roboter - ImmobilienScout24" in chaptcha_part or "Sign in to your account" in chaptcha_part:
        # recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="Ich bin kein Roboter - ImmobilienScout24"]')
        # solver.click_recaptcha_v2(iframe=recaptcha_iframe)
        # input("Please solve the captcha or login. Then press any key to continue.")
        logging.info("waiting for captcha to be solved...")
        return False
    else: 
        return True


def cast_data(df: pd.DataFrame, config: dict):
    if hasattr(config, "cast"):
        cast_config = config.cast
        for key, value in cast_config.items():
            logging.info(f"Cast to type: {key}")
            for column in value:
                if column in df.columns:
                    df[column] = df[column].apply(pd.to_numeric, downcast=key, errors="coerce")
                else:
                    logging.info(f"skip {column}")
    return df

def get_pages_number(driver: webdriver.Chrome, url: str):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
        for _ in range(5):
            # html = driver.page_source
            html = driver.get_page_source()
            if captcha_check(html, driver):       
                break
            WebDriverWait(driver, 10)
        soup = BeautifulSoup(html, 'html.parser')
        pagination_buttons = soup.find_all(class_="Pagination_pagination-button__FFMlW")
        num_page = 1
        for button in pagination_buttons:
            try:
                value = int(button.text)
                if num_page == 1 or value > num_page:
                    num_page = value
            except ValueError:
                continue
    except Exception as e:
        logging.error(f"error occurred: {e}")
        num_page = 1
    return num_page

def parse_expose_link(html: str):
    pattern = re.compile(r'<a\s+[^>]*href="(/expose/\d+[^"]*)"[^>]*>', re.IGNORECASE)
    matches = re.findall(pattern, html)
    unique_matches = set(matches)
    return list(unique_matches)

def find_element_text(soup, tag, class_name=None):
    element = soup.find(tag, class_=class_name)
    if element:
        return element.get_text()
    else:
        return None

def save_single_image(url, path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as file:
                file.write(response.content)
        else:
            logging.error(f"Failed to save image from {url}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error occured in saving single image: {e}")

def save_all_images(exposeId):
    url = f"https://static-immobilienscout24.de/ai-image-api/public/getImages?exposeId={exposeId}"
    try:
        response = requests.get(url, timeout=10)
        res = response.json()
        exposeId = res.get("exposeId")
        for index, item in enumerate(res.get("images")):
            logging.info(f"saving {index} image for expose {exposeId}")
            os.makedirs(f"data/images/{exposeId}", exist_ok=True)
            save_single_image(item.get("originalImage"), f"data/images/{exposeId}/{exposeId}_{index}_original.png")
            for key, value in item.get("generatedImages").items():
                save_single_image(value, f"data/images/{exposeId}/{exposeId}_{index}_{key}.png")
    except Exception as e:
        logging.error(f"Failed to save images for exposeId {exposeId}: {e}")

def scraping():
    cities = configs.urls
    # options = webdriver.ChromeOptions()
    # options.add_argument("--ignore-certificate-errors")
    # options.add_argument("--ignore-ssl-errors")
    # driver = webdriver.Chrome(options=options)

    # with SB(uc=True, headed=True) as driver:
    with Driver(browser="chrome", uc=True, headless=True) as driver:
        # input("changing setting...")
        try:
            for city in cities:
                result_file = f"{configs.out_dir}{city}_{datetime.now().strftime('%Y%m%d')}.csv"
                df_city = pd.DataFrame()
                for url in cities[city]:
                    number_of_pages = get_pages_number(driver=driver, url=url)
                    logging.info(f"number of page in {url}: {number_of_pages}")
                    for i in range(1, number_of_pages + 1):
                        if i == 2:  # for test purposes
                            break
                        logging.info(f"reading page: {i}")
                        if i == 1:
                            driver.get(f"{url}")
                        else:
                            driver.get(f"{url}{i}")
                        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
                        for _ in range(5):
                            # html_page = driver.page_source
                            html_page = driver.get_page_source()
                            if captcha_check(html_page, driver):
                                break
                            WebDriverWait(driver, 10)
                        exposes = parse_expose_link(html=html_page)
                        logging.info(f"number of exposes on page {i}: " + str(len(exposes)))
                        for index, expose in enumerate(exposes):
                            expose_id = expose.split("/")[-1]
                            logging.info(f"extracting data from expose {expose_id}")
                            sub_url = f"https://www.immobilienscout24.de{expose}"
                            # save_all_images(expose_id)
                            driver.get(sub_url)
                            WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
                            for _ in range(5):
                                # html_expose = driver.page_source
                                html_expose = driver.get_page_source()
                                if captcha_check(html_expose, driver):                
                                    break
                                time.sleep(1)
                                WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
                            ####
                            # file_path = f"output_{index}.txt"
                            # with open(file_path, 'w') as file:
                            #     file.write(html_expose)
                            ####
                            expose_json = html_expose.split("keyValues = ")[1].split(r"};")[0] + r'}'
                            online_since = html_expose.split('exposeOnlineSince: "')[1].split(r'",')[0]
                            # title = html_expose.split(r"</title>")[0].split(r"<title>")[1]
                            soup = BeautifulSoup(html_expose, 'html.parser')
                            title = find_element_text(soup, 'title')
                            description = find_element_text(soup, 'pre', class_name='is24qa-objektbeschreibung text-content short-text')
                            equipments = find_element_text(soup, 'pre', class_name='is24qa-ausstattung text-content short-text')
                            locations = find_element_text(soup, 'pre', class_name='is24qa-lage text-content short-text')

                            expose_dict = json.loads(expose_json)
                            expose_dict.update({
                                "url": sub_url,
                                "extract_date": datetime.now().strftime("%Y-%m-%d"),
                                "extract_time": datetime.now().strftime("%H:%M:%S"),
                                "online_since": online_since,
                                "title": title,
                                "description": description,
                                "equipments": equipments,
                                "locations": locations
                            })

                            df_expose = pd.DataFrame([expose_dict])
                            df_city = pd.concat([df_city, df_expose], ignore_index=True)

                df_city.drop_duplicates(subset="url", inplace=True, keep="last")
                df_city = cast_data(df=df_city, config=configs)
                df_city = cal_stats(df=df_city, config=configs)
                df_city.to_csv(result_file, index=False)
        except Exception as e:
            logging.error(f"error occurred during scraping: {e}.")

if __name__ == "__main__":
    scraping()
