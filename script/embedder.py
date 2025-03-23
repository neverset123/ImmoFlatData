import os
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from lancedb.embeddings import with_embeddings
from openai import AzureOpenAI
from dotenv import load_dotenv
import pandas as pd
from config import configs
import numpy as np

load_dotenv()
os.environ["OPENAI_API_VERSION"] = os.getenv("API_VERSION")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("APIKEY")

func = (get_registry()
        .get("openai")
        .create(name=os.getenv("EMBEDDING_MODEL"), use_azure=True))
class Listing(LanceModel):
    description: str = func.SourceField()
    vector: Vector(func.ndims()) = func.VectorField()

def text2vec(df, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("property_listing", 
                            schema=Listing, 
                            mode="overwrite",
                            on_bad_vectors="fill",
                            fill_value="")
    table.add(df.fillna("").to_dict("records"))
    print(table.head().to_pandas())

if __name__ == "__main__":
    db_name = "./lancedb"
    selected_cols = ["description"]
    for city in configs.urls:
        file_path = f"{configs.out_dir}{city}.csv"
        df = pd.read_csv(file_path, usecols=selected_cols, nrows=100) # test on first 10 rows
        text2vec(df, db_name)