import os
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from dotenv import load_dotenv
import pandas as pd
from config import configs

load_dotenv()
os.environ["OPENAI_API_VERSION"] = os.getenv("API_VERSION")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("APIKEY")

func = (get_registry()
        .get("openai")
        .create(name=os.getenv("EMBEDDING_MODEL"), use_azure=True))
class Listing(LanceModel):
    obj_scoutId: int
    title: str
    obj_purchasePrice: int
    description: str = func.SourceField()
    obj_typeOfFlat: str
    obj_privateOffer: bool
    obj_condition: str
    online_since: str
    obj_energyEfficiencyClass: str
    obj_firingTypes: str
    obj_telekomInternetSpeed: str
    obj_rented: str
    url: str
    geo_bg: str
    obj_livingSpace: float
    obj_yearConstructed: int
    obj_picture: str
    vector: Vector(func.ndims()) = func.VectorField()

# datasets of the order of ~100K vectors don't require index creation
def text2vec(df, db_name):
    db = lancedb.connect(db_name)
    table = db.create_table("property_listing", 
                            schema=Listing, 
                            mode="overwrite",
                            on_bad_vectors="fill",
                            fill_value="")
    table.add(df.to_dict("records"))
    print(f"{len(df)} records are embedded!")
    print(table.head().to_pandas())

if __name__ == "__main__":
    db_name = "./lancedb"
    default_fill_values = {
        'int': 0,          # Fill NaN with 0 for integer columns
        'float': 0.0,  # Fill NaN with 0.0 for float columns
        'object': '',      # Fill NaN with empty string for string columns
        'bool': False      # Fill NaN with False for boolean columns
    }
    selected_cols = ["obj_scoutId", "title", "obj_purchasePrice", "description", "obj_typeOfFlat", "obj_privateOffer", "online_since", "obj_energyEfficiencyClass", "obj_firingTypes", "obj_telekomInternetSpeed", "obj_rented", "url", "geo_bg", "obj_livingSpace", "obj_yearConstructed", "obj_condition", "obj_picture"]
    for city in configs.urls:
        file_path = f"{configs.out_dir}{city}.csv"
        file_path_pkl = f"{configs.out_dir}{city}.pkl"
        # df = pd.read_csv(file_path, usecols=selected_cols, nrows=100).drop_duplicates()
        df = pd.read_pickle(file_path_pkl)[selected_cols].head(100)
        df["obj_picture"] = df["obj_picture"].str.split("/ORIG").str[0]
        df[df.select_dtypes(include=['int']).columns] = df.select_dtypes(include=['int']).fillna(default_fill_values['int'])
        df[df.select_dtypes(include=['float']).columns] = df.select_dtypes(include=['float']).fillna(default_fill_values['float'])
        df[df.select_dtypes(include=['object']).columns] = df.select_dtypes(include=['object']).fillna(default_fill_values['object'])
        df[df.select_dtypes(include=['bool']).columns] = df.select_dtypes(include=['bool']).fillna(default_fill_values['bool'])
        text2vec(df, db_name)