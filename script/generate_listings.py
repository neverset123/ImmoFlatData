"""Regenerate listings.json for the frontend from the CSV data."""
import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(ROOT_DIR, "data", "Stuttgart.csv")
OUT_PATH = os.path.join(ROOT_DIR, "app", "frontend", "public", "listings.json")


def main():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scout_id = row.get("obj_scoutId", "")
            pic_count = int(row.get("obj_picturecount", "0") or "0")
            if not scout_id or pic_count == 0:
                continue
            obj_picture_raw = row.get("obj_picture", "")
            obj_picture = ""
            if obj_picture_raw:
                try:
                    pic_dict = eval(obj_picture_raw)
                    url = pic_dict.get("urlScaleAndCrop", "")
                    url = url.split("/ORIG")[0]
                    obj_picture = url
                except Exception:
                    obj_picture = obj_picture_raw.split("/ORIG")[0]
            rows.append({
                "id": scout_id,
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "price": row.get("obj_purchasePrice", ""),
                "rooms": row.get("obj_noRooms", ""),
                "area": row.get("obj_livingSpace", ""),
                "location": row.get("obj_regio4", "") or row.get("geo_ot", ""),
                "district": row.get("obj_regio3", ""),
                "zipCode": row.get("obj_zipCode", ""),
                "floor": row.get("obj_floor", ""),
                "yearBuilt": row.get("obj_yearConstructed", ""),
                "condition": row.get("obj_condition", ""),
                "pictureCount": pic_count,
                "imageUrl": obj_picture if obj_picture else f"https://pictures.immobilienscout24.de/listings/{scout_id}-0.jpg",
                "exposeUrl": f"https://www.immobilienscout24.de/expose/{scout_id}",
                "type": row.get("obj_immotype", ""),
                "balcony": row.get("obj_balcony", "") == "y",
                "garden": row.get("obj_garden", "") == "y",
                "cellar": row.get("obj_cellar", "") == "y",
                "lift": row.get("obj_lift", "") == "y",
                "parking": row.get("obj_parkingSpace", "") != "no_information",
            })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    print(f"Total listings: {len(rows)}")
    print(f"With obj_picture: {sum(1 for r in rows if 'pictures.immobilienscout24' not in r['imageUrl'])}")
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()
