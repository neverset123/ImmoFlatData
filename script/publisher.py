from notion_client import Client
from dotenv import load_dotenv
import lancedb
from lancedb.pydantic import LanceModel, Vector
import pandas as pd
import openai
import os
import json
import pandas as pd
import notion_df

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
    return df

def save_preference(df, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("preference", 
                            schema=Preference, 
                            mode="overwrite",
                            on_bad_vectors="fill",
                            fill_value="")
    table.add(df.fillna("").to_dict("records"))
    print(table.head().to_pandas())


def embed_func(c): 
    client = openai.AzureOpenAI()   
    response = client.embeddings.create(input=c, model=os.getenv("EMBEDDING_MODEL"))
    return [data.embedding for data in response.data]

def find_match(df):
    db = lancedb.connect("./lancedb")
    table_name = "property_listing"
    table = db.open_table(table_name)
    preference_text = " ".join(df["user_input"].tolist())
    preference_embedded = embed_func(preference_text)[0]
    df_matched = table.search(preference_embedded).metric("cosine").limit(5).where("description!=''", prefilter=True).to_pandas()
    return df_matched

# There is still an pydantic version issue
def update_property(df_matched, page_url, api_key):
    notion_df.pandas()
    # df = pd.read_notion(page_url, api_key=api_key)
    # print(df.loc[0,"Summary"])
    # print(df.loc[0, "Included utilities label"])
    df = (df_matched.rename(columns={"obj_privateOffer":"Private Offer",
                            "obj_firingTypes":"Firing Type",
                            "obj_rented":"Rented",
                            "geo_bg":"Location",
                            "url":"Link",
                            "obj_immotype":"Property Type",
                            "obj_purchasePrice":"Purchase Price",
                            "obj_yearConstructed":"Construction Year",
                            "obj_telekomInternetSpeed":"Internet Speed",
                            "obj_energyType":"Energy Type",
                            "obj_usableArea":"Property Size",
                            "online_since":"Online Date",
                            "title":"Title"
                            })
                    [['Title', 'Purchase Price', 'Property Type', 'Private Offer', 'Online Date', 'Energy Type', 'Firing Type', 'Internet Speed', 'Rented', 'Link', 'Location', 'Property Size', 'Construction Year']]
                    )
    df["Title"] = df["Title"].astype("str")
    df["Person"] = "1a4d872b-594c-8186-ac25-0002808c107a"
    df["Online Date"] = pd.to_datetime(df["Online Date"])
    page_url = "https://www.notion.so/1bfb0157974680709c7ffd2675184eba?v=1bfb01579746810d8e5b000cae81f18b"
    df.to_notion(page_url, api_key=api_key)

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
    # df = get_preference(notion, DB_PREFERENCE_ID)
    # # save_preference(df, db_name)
    # df_matched = find_match(df)
    # print(df_matched)
    df_matched = pd.read_parquet("./test.parquet")
    update_property(df_matched, page_url, NOTION_TOKEN)


