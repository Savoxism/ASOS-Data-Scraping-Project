import json
import time
import csv
import logging
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils import get_image_sources_from_thumbnails, safe_click 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', filename='logs/scrape.log')


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
            logging.info(f"Button clicked successfully at div[{div_num}] for product '{product_name}'.")

            # Description
            ul_element_xpath = paths[div_num]["ul_element"]
            ul_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, ul_element_xpath))
            )
            li_elements = ul_element.find_elements(By.TAG_NAME, "li")
            description = [li.text for li in li_elements]
            # print(f"Description found at div[{div_num}]: {description}")
            logging.info(f"Description found at div[{div_num}]: {description}")

            # Category
            category_xpath = paths[div_num]["category"]
            category_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, category_xpath))
            )
            category = category_element.text
            # print(f"Category found at div[{div_num}]: {category}")
            logging.info(f"Category found at div[{div_num}]: {category}")

            break

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Failed to retrieve category or description using div[{div_num}]. Error: {e}")
            # print(f"Failed to retrieve category or description using div[{div_num}]. Error: {e}")

    if not description or not category:
        # print("Description or category not found for any div variant.")
        logging.error("Description or category not found for any div variant.")
        return None, None
    
    return image_urls, product_name, price, category, description

def scraping(product):
    chromedriver_path_win = "C:\\Program Files\\Executables\\chromedriver.exe"
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(service=Service(chromedriver_path_win), options=chrome_options)
    
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


def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def read_product_urls_from_csv(filename, num_products=700):
    from random import sample
    products = []
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        products = [{"product_id": row["product_id"], "product_url": row["url"]} for row in reader]
    return sample(products, num_products) if len(products) >= num_products else products

def main():
    csv_files = ["cat_csv/women/women folder/cat_csv/women_cat/asos_loungewear.csv", "cat_csv/women/women folder/cat_csv/women_cat/asos_shorts.csv", "cat_csv/women/women folder/cat_csv/women_cat/asos_tops.csv", "cat_csv/women/women folder/cat_csv/women_cat/asos_trousers_leggings.csv"]
    for csv_file in csv_files:
        category_name = csv_file.split("/")[-1].split(".")[0]
        
        # Read product URLs
        products = read_product_urls_from_csv(csv_file, num_products=700)
        logging.info(f"Scraping {len(products)} products for category '{category_name}'")

        batch_size = 20
        total_data = []
        
    # Increase the number of cores used for multiprocessing
        num_cores = min(cpu_count(), 10)  
        with Pool(processes=num_cores) as pool:
            for i in tqdm(range(0, len(products), batch_size), desc=f"Scraping {category_name}"):
                batch = products[i:i + batch_size]
                batch_data = pool.map(scraping, batch)

                # Filter out None results and add to total data
                batch_data = [data for data in batch_data if data is not None]
                total_data.extend(batch_data)
                
                # Save batch incrementally to avoid data loss
                save_to_json(total_data, f"product_json/in_progress_{category_name}.json")
        
        # Final save after all batches complete
        final_file = f"product_json/export_{category_name}.json"
        save_to_json(total_data, final_file)
        logging.info(f"Scraping complete for '{category_name}'. Total products scraped: {len(total_data)}")

        print(f"Scraping complete for '{category_name}'. Total products scraped: {len(total_data)}")
        
        
if __name__ == "__main__":
    main()
