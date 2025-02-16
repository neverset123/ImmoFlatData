from dataclasses import dataclass, field
from typing import List, Dict
import yaml

@dataclass
class Config:
    urls: Dict[str, List[str]]
    out_dir: str
    cast: Dict[str, List[str]]
    stat_cols: Dict[str, str]

configs = Config(
    urls={"Stuttgart": 
          ["https://www.immobilienscout24.de/Suche/radius/wohnung-kaufen?centerofsearchaddress=Stuttgart;;;;;;&geocoordinates=48.77711;9.18077;10.0&enteredFrom=result_list&sorting=2&pagenumber=",
            ]},
    out_dir="data/",
    cast={
        "float": 
        [
        # "obj_rentSubsidy",
    ]},
    stat_cols={
        "price_per_space": "df['obj_purchasePrice'] / df['obj_livingSpace']",
        "space_per_room": "df['obj_livingSpace'] / df['obj_noRooms']",
    }
)