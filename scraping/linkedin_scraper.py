import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from scraping.webdriver_manager import WebDriverManager
from scraping.html_parser import LinkedInHTMLParser

class LinkedInScraper:
    def __init__(self, headless=True):
        self.driver_manager = WebDriverManager(headless=headless)
        self.parser = LinkedInHTMLParser()
        
    def search_jobs(self, job_title="", location="", max_pages=3):
        try:
            print(f"Searching for '{job_title}' in '{location}'...")
            
            driver = self.driver_manager.get_driver()
            
            # Go to LinkedIn jobs
            driver.get("https://www.linkedin.com/jobs/search/")
            time.sleep(random.uniform(2, 4))
            
            # Fill search fields
            if job_title:
                title_input = self.driver_manager.wait_for_element(By.CSS_SELECTOR, 'input[aria-label*="Search by title"]')
                if title_input:
                    title_input.clear()
                    title_input.send_keys(job_title)
                    
            if location:
                location_input = self.driver_manager.wait_for_element(By.CSS_SELECTOR, 'input[aria-label*="City"]')
                if location_input:
                    location_input.clear()
                    location_input.send_keys(location)
                    
            # Submit search
            if job_title and title_input:
                title_input.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            # Scrape pages
            all_jobs = []
            for page in range(max_pages):
                print(f"Scraping page {page + 1}...")
                
                page_source = driver.page_source
                jobs = self.parser.parse_job_listings(page_source)
                
                if not jobs:
                    print("No more jobs found")
                    break
                    
                all_jobs.extend(jobs)
                print(f"Found {len(jobs)} jobs on page {page + 1}")
                
                # Go to next page
                if page < max_pages - 1:
                    next_btn = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Next"]')
                    if next_btn and next_btn[0].is_enabled():
                        next_btn[0].click()
                        time.sleep(random.uniform(3, 5))
                    else:
                        break
                        
            print(f"Total jobs found: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        finally:
            self.cleanup()
            
    def cleanup(self):
        self.driver_manager.cleanup()