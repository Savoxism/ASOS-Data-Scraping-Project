from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import csv

chromedriver_path_win = "C:\Program Files\Executables\chromedriver.exe"
chromedriver_path_mac = "/usr/local/bin/chromedriver"

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  
chrome_options.add_argument("--disable-webgl") 
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-dev-shm-usage")  
chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
chrome_options.add_argument("--disable-extensions") 
driver = webdriver.Chrome(service=Service(chromedriver_path_win), options=chrome_options)

# Base URL for ASOS catalog page
base_url = "https://www.asos.com/men/polo-shirts/cat/?cid=4616&page="
target_product_count = 700  # Target number of products
current_page = 1
total_products = 0
data = []


while total_products < target_product_count:
    url = f"{base_url}{current_page}"
    driver.get(url)
    time.sleep(5)  

    # Scroll down to load all items on the current page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5) 
    
    products = driver.find_elements(By.XPATH, "//section/article")

    for product in products:
        try:
            # Product ID
            product_id_element = product.get_attribute("id")
            if "product-" in product_id_element:
                product_id = product_id_element.split("product-")[-1]
            
            # Product URL
            url_element = product.find_element(By.XPATH, ".//a")
            product_url = url_element.get_attribute("href")
            
            data.append([f"product-{product_id}", product_url])
            total_products += 1
            
            # Stop condition
            if total_products >= target_product_count:
                break
        except Exception as e:
            print(f"An error occurred: {e}")

    current_page += 1

# Save data to CSV
csv_file = "cat_csv/asos_polo_shirts.csv"
with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["product_id", "url"])  
    writer.writerows(data)  

driver.quit()

print(f"Data saved to {csv_file}")
