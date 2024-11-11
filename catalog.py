from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import csv

# Set up the Chrome driver with options
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  
chrome_options.add_argument("--disable-webgl") 
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-dev-shm-usage")  
chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
chrome_options.add_argument("--disable-extensions") 
driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

# Base URL for ASOS catalog page
# base_url = "https://www.asos.com/men/t-shirts-vests/cat/?cid=7616&page="
base_url = "https://www.asos.com/men/hoodies-sweatshirts/cat/?cid=5668&page="
target_product_count = 600  # Target number of products
current_page = 1
total_products = 0
data = []

# Loop through pages until we collect enough products
while total_products < target_product_count:
    # Construct URL for the current page
    url = f"{base_url}{current_page}"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Scroll down to load all items on the current page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # Adjust sleep time based on loading speed

    # Locate all product elements on the current page
    products = driver.find_elements(By.XPATH, "//section/article")

    # Extract product data from each item
    for product in products:
        try:
            # Extract product ID
            product_id_element = product.get_attribute("id")
            if "product-" in product_id_element:
                product_id = product_id_element.split("product-")[-1]
            
            # Extract product URL
            url_element = product.find_element(By.XPATH, ".//a")
            product_url = url_element.get_attribute("href")
            
            # Append data to the list
            data.append([f"product-{product_id}", product_url])
            total_products += 1
            
            # Stop collecting if we reach the target number of products
            if total_products >= target_product_count:
                break
        except Exception as e:
            print(f"An error occurred: {e}")

    # Move to the next page
    current_page += 1

# Save data to CSV
csv_file = "asos_hoodies_sweatshirts.csv"
with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["product_id", "url"])  # Write headers
    writer.writerows(data)  # Write product data

# Close the driver
driver.quit()

print(f"Data saved to {csv_file}")
