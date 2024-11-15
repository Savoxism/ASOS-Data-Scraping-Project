import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(1)
    
def safe_click(driver, button_xpath):
    """ Attempt to click a button using JavaScript if Selenium’s click fails. """
    try:
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, button_xpath)))
        scroll_to_element(driver, button)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)
        return True
    except (TimeoutException, ElementClickInterceptedException, NoSuchElementException):
        # print(f"Failed to click button at {button_xpath}")
        return False
    
def get_largest_image_from_srcset(srcset):
    if not srcset:
        return None
    
    # Split the srcset string into individual images and sizes
    image_candidates = srcset.split(',')
    
    # Extract the URL and size of each image
    largest_image_url = ""
    largest_size = 0
    
    for candidate in image_candidates:
        # Split by space to separate URL and size
        parts = candidate.strip().split(' ')
        if len(parts) == 2:
            image_url = parts[0]
            image_size = int(parts[1].replace('w', ''))  # remove 'w' and convert to int
            
            # Select the largest image
            if image_size > largest_size:
                largest_size = image_size
                largest_image_url = image_url
    
    return largest_image_url

def get_image_sources_from_thumbnails(driver, ul_xpath):
    image_urls = []
    
    # Find all the <li> elements inside the <ul> containing the thumbnails
    ul_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, ul_xpath)))
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    # Extract teh image URL from each <li> element
    for li in li_elements:
        try:
            img_element = li.find_element(By.TAG_NAME, "img")
            image_srcset = img_element.get_attribute("srcset")
            image_src = img_element.get_attribute("src")

            # Extract the largest image from srcset, or fallback to src if srcset is not available
            if image_srcset:
                image_url = get_largest_image_from_srcset(image_srcset)
            else:
                image_url = image_src  # Fallback to src

            if image_url:
                image_urls.append(image_url)
        except Exception as e:
            print(f"Error extracting image from thumbnail: {e}")
        
    return image_urls