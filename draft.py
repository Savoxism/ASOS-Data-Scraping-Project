import json

def count_scraped_products(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return len(data)

# Replace with the path to your JSON file
json_file = "product_json/Hoodies&Sweatshirts/asos_hoodies_sweatchirts_combined.json"
count = count_scraped_products(json_file)
print(f"Number of products scraped: {count}")