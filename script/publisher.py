from notion_client import Client
from dotenv import load_dotenv
import lancedb
from lancedb.pydantic import LanceModel
import pandas as pd
import openai
import os
import pandas as pd
import notion_df
import requests
import json

load_dotenv()
os.environ["OPENAI_API_VERSION"] = os.getenv("API_VERSION")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("APIKEY")

class Preference(LanceModel):
    user_id: str
    user_name: str
    user_input: str

def get_preference(notion, db_id):
    data_pref = notion.databases.query(
        **{
            "database_id": db_id,
        }
    )["results"]
    selected_column = "Criteria"
    columns = ['user_id', 'user_name', 'user_input']
    df = pd.DataFrame(columns=columns)
    for item in data_pref:
        if selected_column in item['properties']:
            data_col = item['properties'][selected_column]["rich_text"]
            user_col = item['properties']["Person"]["people"]
            if len(data_col)!=0:
                user_id = user_col[0]["id"]
                user_name = user_col[0]["name"]
                user_input = data_col[0]['text']['content']
                df = pd.concat([df, pd.DataFrame({'user_id': [user_id], 'user_name': [user_name], 'user_input': [user_input]})], ignore_index=True)
    print(f"Got preference inputs from {df["user_id"].nunique()} users.")
    return df

def save_preference(df, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("preference",
                            schema=Preference,
                            mode="overwrite",
                            on_bad_vectors="fill",
                            fill_value="")
    table.add(df.fillna("").to_dict("records"))
    print("saved user preferences into db.")
    # print(table.head().to_pandas())

def embed_func(c):
    client = openai.AzureOpenAI()
    response = client.embeddings.create(input=c, model=os.getenv("EMBEDDING_MODEL"))
    return [data.embedding for data in response.data]

def find_match(df):
    db = lancedb.connect("./lancedb")
    table_name = "property_listing"
    table = db.open_table(table_name)
    df_list = []
    for user_id in df["user_id"].unique():
        preference_text = " ".join(df[df["user_id"]==user_id]["user_input"].tolist())
        preference_embedded = embed_func(preference_text)[0]
        df_matched = table.search(preference_embedded).metric("cosine").limit(10).where("description!=''", prefilter=True).to_pandas()
        df_matched["Person"] = user_id
        df_list.append(df_matched)
        print(f"found {len(df_matched)} matches for user {user_id}.")
    df_combined = pd.concat(df_list)
    df_result = (df_combined.groupby(['obj_scoutId', 'title', 'obj_purchasePrice', 'description',
                                    'obj_typeOfFlat', 'obj_privateOffer', 'obj_condition', 'online_since',
                                    'obj_energyEfficiencyClass', 'obj_firingTypes',
                                    'obj_telekomInternetSpeed', 'obj_rented', 'url', 'geo_bg',
                                    'obj_usableArea', 'obj_yearConstructed', 'obj_picture'], as_index=False)
                            .agg({
                                "Person":list
                            })
                )
    return df_result

def update_db_property_type(api_key, db_id, target_col="Cover image", target_type = "rich_text"):
    url = f"https://api.notion.com/v1/databases/{db_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "properties": {
            target_col: {
                "type": target_type,
                target_type: {}
            }
        }
    }
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print("Image attribute type updated successfully!")
    else:
        print(f"Failed to update image attribute type: {response.status_code}.")

def clear_db_data(api_key, db_id):
    query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(query_url, headers=headers)
    data = response.json()
    for row in data["results"]:
        # if row["properties"]["Acquisition"]["select"] is not None: # keep item that is in purchase process
        #     continue
        page_id = row["id"]
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "archived": True
        }
        update_response = requests.patch(update_url, headers=headers, json=payload)
        if update_response.status_code == 200:
            print(f"Successfully archived for page {page_id}.")
        else:
            print(f"Failed to archive page {page_id}: {update_response.status_code}.")
            print(update_response.json())

def update_db(df_matched, page_url, api_key):
    notion_df.pandas()
    df = (df_matched.rename(columns={"obj_privateOffer":"Private Offer",
                            "obj_picture":"Cover image",
                            "obj_firingTypes":"Firing Type",
                            "obj_rented":"Rented",
                            "geo_bg":"Location",
                            "url":"Link",
                            "obj_typeOfFlat":"Property Type",
                            "obj_purchasePrice":"Purchase Price",
                            "obj_yearConstructed":"Construction Year",
                            "obj_telekomInternetSpeed":"Internet Speed",
                            "obj_energyEfficiencyClass":"Energy Class",
                            "obj_usableArea":"Property Size",
                            "online_since":"Online Date",
                            "title":"Title",
                            "obj_condition":"Property Condition"
                            })
                    [['Title', 'Purchase Price', 'Property Type', 'Private Offer', "Cover image", 'Property Condition', 'Online Date', 'Energy Class', 'Firing Type', 'Internet Speed', 'Rented', 'Link', 'Location', 'Property Size', 'Construction Year', 'Person']]
                    )
    df["Title"] = df["Title"].astype("str")
    df["Online Date"] = pd.to_datetime(df["Online Date"])
    df["Rented"] = df["Rented"].apply(lambda x: True if x =="y" else False)
    df.to_notion(page_url, api_key=api_key)
    print("Property list is updated!")

if __name__ == "__main__":
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.width', None)
    # pd.set_option('display.max_colwidth', None)
    db_name = "./lancedb"
    load_dotenv()
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DB_PREFERENCE_ID = os.getenv("DB_PREFERENCE_ID")
    DB_PROPERTY_ID = os.getenv("DB_PROPERTY_ID")
    page_url = os.getenv("DB_PROPERTY_PAGE_URL")
    notion = Client(auth=NOTION_TOKEN)
    df_pref = get_preference(notion, DB_PREFERENCE_ID)
    df_matched = find_match(df_pref)
    clear_db_data(NOTION_TOKEN, DB_PROPERTY_ID)
    update_db_property_type(NOTION_TOKEN, DB_PROPERTY_ID, target_type="rich_text")
    update_db(df_matched, page_url, NOTION_TOKEN)
    update_db_property_type(NOTION_TOKEN, DB_PROPERTY_ID, target_type="files")


