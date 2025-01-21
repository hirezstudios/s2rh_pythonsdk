import csv
import json
import re

def parse_id_and_legacy_id(id_string):
    """
    Given a string like (Id=00000000000000000000000000000095,LegacyId=149),
    return ("00000000000000000000000000000095", "149").
    """
    match = re.search(r"\(Id=([^,]+),LegacyId=(.+)\)", id_string)
    if not match:
        return None, None
    return match.group(1), match.group(2)

def parse_stat_tags(stat_tags_string):
    """
    Given a string like ((StatTag=(TagName="Character.Stat.PhysicalPower"),Value=45.000000),...),
    parse it into a list of {'TagName': 'Character.Stat.PhysicalPower', 'Value': 45.0}.
    """
    # Each stat is wrapped in parentheses. We'll capture each (StatTag=...,Value=...)
    stats = []
    # Find all occurrences of (StatTag=(TagName="..."),Value=...)
    stat_pattern = re.compile(
        r"\(StatTag=\(TagName=\"([^\"]+)\"\),Value=([\d\.]+)\)"
    )
    for tag, val in stat_pattern.findall(stat_tags_string):
        stats.append({
            "TagName": tag,
            "Value": float(val)
        })
    return stats

def main():
    items = []
    with open("items.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty/short lines
            if len(row) < 7:
                continue

            internal_name       = row[0].strip()
            id_legacy_string    = row[1].strip()
            display_name        = row[2].strip()
            item_type           = row[3].strip()
            gameplay_tags       = row[4].strip()
            passive_description = row[5].strip()  # This might be empty depending on the item
            stat_tags_string    = row[6].strip()  # This might be empty as well

            item_id, legacy_id = parse_id_and_legacy_id(id_legacy_string)

            # Combine display name and passive/active text in a single "Description" 
            # (in a real game, you might split these further).
            description = f"{passive_description}" if passive_description else ""

            # Parse stat tags into a structured list
            stats = parse_stat_tags(stat_tags_string)

            item_data = {
                "Item_Id": item_id,
                "Legacy_Id": legacy_id,
                "DisplayName": display_name,
                "Description": description,
                "Stats": stats
            }
            items.append(item_data)

    # Example: write out to a JSON file
    with open("items.json", "w", encoding="utf-8") as json_out:
        json.dump(items, json_out, indent=2, ensure_ascii=False)

    print("JSON export complete. Check items.json for results.")

if __name__ == "__main__":
    main()
