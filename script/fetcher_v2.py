from datetime import datetime
import pandas as pd
from config import configs
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def cal_stats(df: pd.DataFrame, config: dict):
    for col, formula in config.stat_cols.items():
        if col in df.columns:
            df[col] = eval(formula)
        else:
            logging.info(f"skip {col} stat")
    return df

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

def post_request(url, data={"supportedResultListType":[],"userData":{}}, headers={"Connection": "keep-alive", "User-Agent": "ImmoScout_27.12_26.2_._",  "Accept": "application/json", "Content-Type": "application/json"}):
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def get_request(url, headers={"User-Agent": "ImmoScout_27.12_26.2_._",  "Accept": "application/json"}):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def scraping():
    cities = configs.api_urls
    try:
        for city in cities:
            result_file = f"{configs.out_dir}{city}.csv"
            result_file_pkl = f"{configs.out_dir}{city}.pkl"
            df_city = pd.DataFrame()
            for url in cities[city]:
                page_results = post_request(url)
                number_of_pages = page_results.get('numberOfPages', 0)
                logging.info(f"number of page in {url}: {number_of_pages}")
                for i in range(1, min(number_of_pages + 1, 21)): # limit page number to be 21 to reduce scraping time
                    # if i == 2:  # for test purposes
                    #     break
                    if i > 1:
                        page_results = post_request(f"{url}{i}")
                    logging.info(f"reading page: {i}")
                    page_size = page_results.get('pageSize', 0)
                    expose_ids = [expose.get('item', {}).get('id', 0) for expose in page_results.get('resultListItems', [])]
                    expose_titles = [expose.get('item', {}).get('title', "") for expose in page_results.get('resultListItems', [])]
                    expose_pics = [expose.get('item', {}).get('pictures', []) for expose in page_results.get('resultListItems', [])]
                    logging.info(f"number of exposes on page {i}: {page_size}")
                    for index, expose_id in enumerate(expose_ids):
                        logging.info(f"extracting data from expose {expose_id}")
                        sub_url = f"https://api.mobile.immobilienscout24.de/expose/{expose_id}"
                        # save_all_images(expose_id)
                        expose_results = get_request(sub_url)
                        expose_sections = expose_results.get('sections', [])
                        expose_dict = expose_results.get('adTargetingParameters', {})
                        online_since = ([section.get('onlineSince', '') for section in expose_sections if section.get('title') == 'Plus Mitglieder wissen mehr!'] or [''])[0]
                        title = expose_titles[index]
                        description = ([section.get('text', '') for section in expose_sections if section.get('title') == 'Objektbeschreibung'] or [''])[0]
                        equipments = ([section.get('text', '') for section in expose_sections if section.get('title') == 'Ausstattung'] or [''])[0]
                        locations = ([section.get('text', '') for section in expose_sections if section.get('title') == 'Lage'] or [''])[0]
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
            if not df_city.empty:
                df_city.to_csv(result_file, index=False)
                df_city.to_pickle(result_file_pkl)
    except Exception as e:
        logging.error(f"error occurred during scraping: {e}.")

if __name__ == "__main__":
    scraping()