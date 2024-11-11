import json
import time
import csv
from multiprocessing import Pool, cpu_count
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils import get_image_sources_from_thumbnails, safe_click  


def scrape_info_on_page(driver):
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(2)
    
    # Image URLs
    ul_xpath = "/html/body/div[1]/div/main/div[3]/section/div/div[1]/div/div[1]/ul"
    image_urls = get_image_sources_from_thumbnails(driver, ul_xpath)
    
    # Product Name
    product_name_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[1]/h1"))
    )
    product_name = product_name_element.text
    
    # Price
    price_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[2]/div/span[2]"))
    )
    price = price_element.text
    
    # Description and category
    description = []
    category = None

    paths = {
        6: {
            "button": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/h2/button",
            "ul_element": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/div/div/div/ul",
            "category": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/div/div/div/a[1]/strong"
        },
        7: {
            "button": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/h2/button",
            "ul_element": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/div/div/div/ul",
            "category": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/div/div/div/a[1]/strong"
        },
        8: {
            "button": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/h2/button",
            "ul_element": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/div/div/div/ul",
            "category": "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/div/div/div/a[1]/strong"
        }
    }

    for div_num in [6, 7, 8]:
        button_xpath = paths[div_num]["button"]
        # print(f"Attempting to use button XPath for div[{div_num}]: {button_xpath}")
        try:
            button_xpath = paths[div_num]["button"]
            if not safe_click(driver, button_xpath):
                continue
            # print(f"Button clicked successfully at div[{div_num}] for product '{product_name}'.")

            # Description
            ul_element_xpath = paths[div_num]["ul_element"]
            ul_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, ul_element_xpath))
            )
            li_elements = ul_element.find_elements(By.TAG_NAME, "li")
            description = [li.text for li in li_elements]
            # print(f"Description found at div[{div_num}]: {description}")

            # Category
            category_xpath = paths[div_num]["category"]
            category_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, category_xpath))
            )
            category = category_element.text
            # print(f"Category found at div[{div_num}]: {category}")

            break

        except (TimeoutException, NoSuchElementException) as e:
            print(f"Failed to retrieve category or description using div[{div_num}]. Error: {e}")

    if not description or not category:
        print("Description or category not found for any div variant.")
        return None, None
    
    return image_urls, product_name, price, category, description

def scraping(product):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)
    
    try: 
        driver.get(product["product_url"])        
        image_urls, product_name, price, category, description = scrape_info_on_page(driver)
        
        product_info = {
            "product_id": product["product_id"],
            "product_url": product["product_url"],
            "product_name": product_name,
            "price": price,
            "description": description,
            "image_urls": image_urls,
            "category": category,
        }
        
    except Exception as e:
        print(f"Error scraping product {product['product_id']}: {e}")
        product_info = None
    finally:
        driver.quit()
        
    return product_info


def save_to_json(data, output_file="asos_shirt_vest.json"):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def read_product_urls_from_csv(filename, start=0, limit=100):
    products = []
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < start:
                continue  
            if i >= start + limit:
                break 
            products.append({"product_id": row["product_id"], "product_url": row["url"]})
    return products

def main():
    csv_file = "cat_csv/asos_hoodies_sweatshirts.csv"
    products = read_product_urls_from_csv(csv_file, start=500, limit=100)  

    with Pool(processes=cpu_count()) as pool:
        scraped_data = pool.map(scraping, products)
    
    # # Filter out any None values if scraping failed for some products
    # scraped_data = [data for data in scraped_data if data is not None]
    
    # Save the scraped data to a JSON file
    save_to_json(scraped_data, "product_json/Hoodies&Sweatshirts/asos_hoodies_sweatshirts_501_600.json")

if __name__ == "__main__":
    main()
