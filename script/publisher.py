from notion_client import Client
from dotenv import load_dotenv
import lancedb
from lancedb.pydantic import LanceModel, Vector
import pandas as pd
import openai
import os

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
    # preference_text = " ".join(df["user_input"].tolist())
    preference_text = "Herzlich willkommen in Fellbach-Schmiden. \n\nIhr neues Zuhause befindet sich am Ortsrand in einem ruhigen und sonnigen Wohngebiet. Sie wohnen und leben mit hohem Naherholungswert nahezu im Grünen in der Nähe des Schmidener Felds.\n\nDie Ortsmitte von Fellbach-Schmiden erreichen Sie zu Fuß oder mit dem Auto in wenigen Minuten. Dort finden Sie zusätzlich zu den Geschäften für den täglichen Bedarf Arztpraxen, Apotheken und weitere Gesundheitsdienstleister"
    preference_embedded = embed_func(preference_text)[0]
    df_matched = table.search(preference_embedded).metric("cosine").limit(3).to_pandas()
    return df_matched

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    db_name = "./lancedb"
    load_dotenv()
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DB_PREFERENCE_ID = os.getenv("DB_PREFERENCE_ID")
    notion = Client(auth=NOTION_TOKEN)
    df = get_preference(notion, DB_PREFERENCE_ID)
    # save_preference(df, db_name)
    df_matched = find_match(df)
    print(df_matched)


