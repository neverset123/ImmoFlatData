from notion_client import Client
from dotenv import load_dotenv
import lancedb
from lancedb.pydantic import LanceModel, Vector
import pandas as pd
import os

class Preference(LanceModel):
    user_id: str
    user_name: str
    user_input: str

def get_preference(notion, db_id):
    data_pref = notion.databases.query(
        **{
            "database_id": db_id,
        }
    )
    return data_pref

def save_preference(df, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("preference", 
                            schema=Preference, 
                            mode="overwrite",
                            on_bad_vectors="fill",
                            fill_value="")
    table.add(df.fillna("").to_dict("records"))
    print(table.head().to_pandas())

if __name__ == "__main__":
    db_name = "./lancedb"
    load_dotenv()
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DB_PREFERENCE_ID = os.getenv("DB_PREFERENCE_ID")
    notion = Client(auth=NOTION_TOKEN)
    data = get_preference(notion, DB_PREFERENCE_ID)["results"]
    selected_column = "Criteria"
    columns = ['user_id', 'user_name', 'user_input']
    df = pd.DataFrame(columns=columns)
    for item in data:
        if selected_column in item['properties']:
            data_col = item['properties'][selected_column]["rich_text"]
            user_col = item['properties']["Person"]["people"]
            if len(data_col)!=0:
                user_id = user_col[0]["id"]
                user_name = user_col[0]["name"]
                user_input = data_col[0]['text']['content']
                df = pd.concat([df, pd.DataFrame({'user_id': [user_id], 'user_name': [user_name], 'user_input': [user_input]})], ignore_index=True)

    save_preference(df, db_name)
