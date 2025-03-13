import os
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import with_embeddings
from openai import AzureOpenAI
from dotenv import load_dotenv
import pandas as pd
from config import configs

load_dotenv()

EMBEDDING_MODEL_NAME = "text-embedding-ada-002"
client = AzureOpenAI(
    api_version=os.getenv("API_VERSION"),
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("APIKEY")
)
class Listing(LanceModel):
    vector: Vector(384)
    description: str

def embed_func(input_text):
    if pd.isna(input_text):
        return []    
    response = client.embeddings.create(
            input=input_text, 
            model=os.getenv("EMBEDDING_MODEL")
        )
    return [data.embedding[:384] for data in response.data] # reduce dimension for speed

def text2vec(df, col, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("property_listing", schema=Listing, mode="overwrite")
    df_embedded = with_embeddings(embed_func, df, column=col, batch_size=1, show_progress=True).to_pandas()
    table.add(df_embedded.to_dict('records'))
    print(table.head().to_pandas())

if __name__ == "__main__":
    db_name = "./lancedb"
    selected_cols = ["description"]
    for city in configs.urls:
        file_path = f"{configs.out_dir}{city}.csv"
        df = pd.read_csv(file_path, usecols=selected_cols, nrows=88) # test on first 10 rows
        for col in selected_cols: 
            text2vec(df, col, db_name)
