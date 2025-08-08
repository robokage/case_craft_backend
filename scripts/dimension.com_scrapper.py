import os
import time
import requests
import random
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # type: ignore




class Scrapper:
    def __init__(self):
        self.base_url = "https://www.dimensions.com"
        self.collection_url = f"{self.base_url}/collection/phones-cell-phones"
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
            
    def get_all_phone_links(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.collection_url)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        container = soup.find('div', class_='combo-grid-list-filter w-dyn-items')
    
        links = {}
        for item in container.find_all('div', attrs={"data-item": "true", "role": "listitem"}): # type: ignore
            a_tag = item.find('a', class_='text-element-title-grid') # type: ignore
            name = a_tag.text.strip() # type: ignore
            if a_tag and a_tag.get('href'): # type: ignore
                links[name] = urljoin(self.base_url, a_tag['href']) # type: ignore
        return links
    
    @staticmethod
    def safe_filename(name):
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)

    def download_file(self, url, filepath):
        try:
            time.sleep(random.uniform(1.5, 3.0))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with self.session.get(url, headers=self.headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            print(f"[!] Failed to download {url} – {e}")

    def get_with_retry(self, url, timeout=15):
        try:
            time.sleep(random.uniform(1.5, 3.0))
            response = self.session.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"[!] Error fetching {url}: {e}")
            return None

    def scrape_phone_data(self, name, link):
        result = {}
        print(f"[+] Scraping: {name}")
        res = self.get_with_retry(link)
        if not res:
            print(f"Could not fetch phone link for {name} with link {link}")
            return

        soup = BeautifulSoup(res.content, "html.parser")
        detail_wrapper = soup.find("div", class_="detail-content-wrapper")
        if not detail_wrapper:
            print(f"[!] Detail section missing for {name}")
            return

        # 1. Extract dimensions & designer
        for wrapper in detail_wrapper.find_all("div", class_="detail-text-item-wrapper"): # type: ignore
            key_div = wrapper.find("div", class_="detail-subtitle") # type: ignore
            val_div = wrapper.find("div", class_="detail-text") # type: ignore
            if key_div and val_div:
                key = key_div.get_text(strip=True).replace(":", "")
                val = val_div.get_text(strip=True)
                result[key] = val

        designer_div = detail_wrapper.find("div", class_="detail-subtitle w-embed", string="Designer:") # type: ignore
        if designer_div:
            designer_text = designer_div.find_next_sibling("div", class_="detail-text")
            if designer_text:
                result["Designer"] = designer_text.get_text(strip=True)

        designer = result.get("Designer", "Unknown")
        folder = os.path.join("output", self.safe_filename(designer))
        filename_base = os.path.join(folder, self.safe_filename(name))

        # 2. Download SVG
        svg_div = soup.find("div", class_="intro-featured-wrapper")
        if not svg_div:
            raise RuntimeError
        if svg_div: 
            img_tag = svg_div.find("img", class_="content-img w-condition-invisible") # type: ignore
            if img_tag and img_tag.get("src", "").endswith(".svg"): # type: ignore
                svg_url = img_tag["src"] # type: ignore
                svg_path = f"{filename_base}.svg"
                self.download_file(svg_url, svg_path)
                
        return result
    
    def run(self):
        all_data = {}
        phone_links = self.get_all_phone_links()
        print("Total phone links found:", len(phone_links))
        for name, link in tqdm(phone_links.items(), desc="Scraping phones"):
            data = self.scrape_phone_data(name, link)
            if data:
                all_data[name] = data

        # Save all scraped data to a file
        with open("phone_metadata.json", "w") as f:
            json.dump(all_data, f, indent=2)
    

if __name__ == "__main__":
    Scrapper().run()