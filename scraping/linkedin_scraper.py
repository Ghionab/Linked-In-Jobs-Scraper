"""
LinkedIn Job Scraper
Core scraping functionality for LinkedIn job search automation
"""

import time
import random
from urllib.parse import urlencode, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

import config
from scraping.webdriver_manager import WebDriverManager
from scraping.html_parser import LinkedInHTMLParser


class LinkedInScraper:
    """Main scraper class for LinkedIn job search automation"""
    
    def __init__(self, headless=True):
        """
        Initialize LinkedIn scraper
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.webdriver_manager = WebDriverManager(headless=headless)
        self.html_parser = LinkedInHTMLParser()
        self.current_search_params = {}
        self.scraped_jobs = []
        
    def search_jobs(self, job_title="", location="", job_type="All", experience_level="All", max_pages=3):
        """
        Perform LinkedIn job search with specified parameters
        
        Args:
            job_title (str): Job title to search for
            location (str): Location to search in
            job_type (str): Type of job (Full-time, Part-time, etc.)
            experience_level (str): Experience level (Entry, Mid, Senior, etc.)
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            list: List of job dictionaries with extracted data
        """
        try:
            print("Starting LinkedIn job search...")
            
            # Store search parameters
            self.current_search_params = {
                'job_title': job_title,
                'location': location,
                'job_type': job_type,
                'experience_level': experience_level
            }
            
            # Clear previous results
            self.scraped_jobs = []
            
            # Navigate to LinkedIn jobs page
            print("Step 1: Navigating to LinkedIn jobs page...")
            if not self._navigate_to_jobs_page():
                print("Failed to navigate to LinkedIn jobs page")
                return []
            
            # Input search parameters
            print("Step 2: Entering search parameters...")
            if not self._input_search_parameters(job_title, location):
                print("Failed to input search parameters")
                return []
            
            # Apply filters
            print("Step 3: Applying filters...")
            if not self._apply_filters(job_type, experience_level):
                print("Failed to apply filters (continuing anyway)")
                # Don't return empty - filters are optional
            
            # Scrape job listings from multiple pages
            print(f"Step 4: Scraping up to {max_pages} pages of job listings...")
            jobs = self._scrape_job_pages(max_pages)
            
            print(f"Job search completed. Found {len(jobs)} total jobs.")
            return jobs
            
        except Exception as e:
            print(f"Error during job search: {str(e)}")
            return []
        finally:
            # Clean up resources
            print("Cleaning up scraper resources...")
            self.cleanup()
    
    def _navigate_to_jobs_page(self):
        """
        Navigate to LinkedIn jobs search page
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            print("Navigating to LinkedIn jobs page...")
            
            # Use the retry mechanism from WebDriverManager
            success = self.webdriver_manager.navigate_to_url_with_retry(
                config.LINKEDIN_JOBS_BASE_URL
            )
            
            if not success:
                print("Failed to navigate to LinkedIn jobs page")
                return False
            
            # Wait for page to load and check for blocking
            page_source = self.webdriver_manager.get_page_source_safe()
            if self.webdriver_manager.is_blocked_or_captcha(page_source):
                print("LinkedIn access blocked or CAPTCHA detected")
                return False
            
            # Wait for search form to be present
            search_form = self.webdriver_manager.wait_for_element_with_retry(
                By.CSS_SELECTOR, 
                'input[data-test-id="jobs-search-box-keyword-id-ember"], input[placeholder*="job title"], input[aria-label*="Search by title"]',
                timeout=15
            )
            
            if not search_form:
                print("Could not find job search form on LinkedIn")
                return False
            
            print("Successfully navigated to LinkedIn jobs page")
            return True
            
        except Exception as e:
            print(f"Error navigating to LinkedIn jobs page: {str(e)}")
            return False
    
    def _input_search_parameters(self, job_title, location):
        """
        Input job title and location into search fields
        
        Args:
            job_title (str): Job title to search for
            location (str): Location to search in
            
        Returns:
            bool: True if input successful, False otherwise
        """
        try:
            driver = self.webdriver_manager.get_driver()
            
            # Find and fill job title field
            if job_title:
                print(f"Entering job title: {job_title}")
                
                # Try multiple selectors for job title input
                title_selectors = [
                    'input[data-test-id="jobs-search-box-keyword-id-ember"]',
                    'input[placeholder*="job title"]',
                    'input[aria-label*="Search by title"]',
                    'input[id*="jobs-search-box-keyword"]',
                    '.jobs-search-box__text-input[placeholder*="title"]'
                ]
                
                title_input = None
                for selector in title_selectors:
                    title_input = self.webdriver_manager.wait_for_element(By.CSS_SELECTOR, selector, timeout=10)
                    if title_input:
                        break
                
                if not title_input:
                    print("Could not find job title input field")
                    return False
                
                # Clear and enter job title
                title_input.clear()
                title_input.send_keys(job_title)
                time.sleep(1)  # Brief pause for input processing
            
            # Find and fill location field
            if location:
                print(f"Entering location: {location}")
                
                # Try multiple selectors for location input
                location_selectors = [
                    'input[data-test-id="jobs-search-box-location-id-ember"]',
                    'input[placeholder*="location"]',
                    'input[aria-label*="City"]',
                    'input[id*="jobs-search-box-location"]',
                    '.jobs-search-box__text-input[placeholder*="location"]'
                ]
                
                location_input = None
                for selector in location_selectors:
                    location_input = self.webdriver_manager.wait_for_element(By.CSS_SELECTOR, selector, timeout=10)
                    if location_input:
                        break
                
                if not location_input:
                    print("Could not find location input field")
                    return False
                
                # Clear and enter location
                location_input.clear()
                location_input.send_keys(location)
                time.sleep(1)  # Brief pause for input processing
            
            # Submit the search
            print("Submitting job search...")
            
            # Try to find and click search button
            search_button_selectors = [
                'button[data-test-id="jobs-search-box-submit-button"]',
                'button[aria-label*="Search"]',
                '.jobs-search-box__submit-button',
                'button[type="submit"]'
            ]
            
            search_button = None
            for selector in search_button_selectors:
                search_button = self.webdriver_manager.wait_for_element(By.CSS_SELECTOR, selector, timeout=10)
                if search_button:
                    break
            
            if search_button:
                search_button.click()
            else:
                # Fallback: press Enter on title input
                if job_title and title_input:
                    from selenium.webdriver.common.keys import Keys
                    title_input.send_keys(Keys.RETURN)
                else:
                    print("Could not find search button or submit search")
                    return False
            
            # Wait for search results to load
            time.sleep(3)
            
            # Check if search was successful
            results_container = self.webdriver_manager.wait_for_element(
                By.CSS_SELECTOR, 
                '.jobs-search__results-list, .scaffold-layout__list-container, .jobs-search-results-list',
                timeout=15
            )
            
            if not results_container:
                print("Search results did not load properly")
                return False
            
            print("Search parameters entered successfully")
            return True
            
        except Exception as e:
            print(f"Error inputting search parameters: {str(e)}")
            return False
    
    def _apply_filters(self, job_type, experience_level):
        """
        Apply job type and experience level filters
        
        Args:
            job_type (str): Job type filter
            experience_level (str): Experience level filter
            
        Returns:
            bool: True if filters applied successfully, False otherwise
        """
        try:
            # Skip if no filters to apply
            if job_type == "All" and experience_level == "All":
                print("No filters to apply")
                return True
            
            print(f"Applying filters - Job Type: {job_type}, Experience: {experience_level}")
            
            driver = self.webdriver_manager.get_driver()
            
            # Wait for filters section to be available
            time.sleep(2)
            
            # Apply job type filter
            if job_type != "All":
                if not self._apply_job_type_filter(job_type):
                    print(f"Failed to apply job type filter: {job_type}")
                    # Continue anyway - filters are not critical
            
            # Apply experience level filter
            if experience_level != "All":
                if not self._apply_experience_filter(experience_level):
                    print(f"Failed to apply experience filter: {experience_level}")
                    # Continue anyway - filters are not critical
            
            # Wait for filtered results to load
            time.sleep(3)
            
            print("Filters applied successfully")
            return True
            
        except Exception as e:
            print(f"Error applying filters: {str(e)}")
            # Return True to continue scraping even if filters fail
            return True
    
    def _apply_job_type_filter(self, job_type):
        """Apply job type filter"""
        try:
            # Look for job type filter options
            job_type_selectors = [
                f'input[value*="{job_type.lower()}"]',
                f'label:contains("{job_type}")',
                f'button:contains("{job_type}")'
            ]
            
            # Try to find and click job type filter
            for selector in job_type_selectors:
                elements = self.webdriver_manager.find_elements_safe(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            time.sleep(1)
                            return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            print(f"Error applying job type filter: {str(e)}")
            return False
    
    def _apply_experience_filter(self, experience_level):
        """Apply experience level filter"""
        try:
            # Map experience levels to LinkedIn's format
            experience_mapping = {
                "Entry": ["entry", "internship", "associate"],
                "Mid": ["mid", "experienced"],
                "Senior": ["senior", "lead"],
                "Executive": ["executive", "director", "vp"]
            }
            
            search_terms = experience_mapping.get(experience_level, [experience_level.lower()])
            
            # Look for experience level filter options
            for term in search_terms:
                selectors = [
                    f'input[value*="{term}"]',
                    f'label:contains("{term}")',
                    f'button:contains("{term}")'
                ]
                
                for selector in selectors:
                    elements = self.webdriver_manager.find_elements_safe(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                time.sleep(1)
                                return True
                        except:
                            continue
            
            return False
            
        except Exception as e:
            print(f"Error applying experience filter: {str(e)}")
            return False
    
    def _scrape_job_pages(self, max_pages):
        """
        Scrape job listings from multiple pages
        
        Args:
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            list: List of job dictionaries
        """
        all_jobs = []
        current_page = 1
        consecutive_empty_pages = 0
        max_empty_pages = 2  # Stop after 2 consecutive empty pages
        
        try:
            while current_page <= max_pages and consecutive_empty_pages < max_empty_pages:
                print(f"Scraping page {current_page} of {max_pages}...")
                
                # Wait for page to fully load
                time.sleep(2)
                
                # Get current page source
                page_source = self.webdriver_manager.get_page_source_safe()
                if not page_source:
                    print(f"Could not get page source for page {current_page}")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= max_empty_pages:
                        break
                    continue
                
                # Check for blocking
                if self.webdriver_manager.is_blocked_or_captcha(page_source):
                    print("Blocking detected, stopping scraping")
                    break
                
                # Parse jobs from current page
                page_jobs = self.html_parser.parse_job_listings(page_source)
                
                if not page_jobs:
                    print(f"No jobs found on page {current_page}")
                    consecutive_empty_pages += 1
                    
                    # Check if we've reached the end of results
                    if "No matching jobs found" in page_source or "0 results" in page_source:
                        print("Reached end of search results")
                        break
                        
                    # Try to continue to next page in case this page had loading issues
                    if current_page < max_pages and consecutive_empty_pages < max_empty_pages:
                        if not self._navigate_to_next_page():
                            print("Could not navigate to next page, stopping")
                            break
                        current_page += 1
                        continue
                else:
                    consecutive_empty_pages = 0  # Reset counter when jobs are found
                    print(f"Found {len(page_jobs)} jobs on page {current_page}")
                    
                    # Filter out duplicate jobs based on ID or URL
                    new_jobs = []
                    existing_ids = {job.get('id') for job in all_jobs}
                    existing_urls = {job.get('url') for job in all_jobs}
                    
                    for job in page_jobs:
                        job_id = job.get('id')
                        job_url = job.get('url')
                        
                        # Skip if we've already seen this job
                        if job_id in existing_ids or job_url in existing_urls:
                            continue
                            
                        new_jobs.append(job)
                        existing_ids.add(job_id)
                        existing_urls.add(job_url)
                    
                    all_jobs.extend(new_jobs)
                    print(f"Added {len(new_jobs)} new unique jobs from page {current_page}")
                
                # Try to navigate to next page
                if current_page < max_pages:
                    if not self._navigate_to_next_page():
                        print("Could not navigate to next page, stopping")
                        break
                
                current_page += 1
                
                # Apply delay between pages
                self.webdriver_manager.apply_request_delay()
            
            print(f"Scraping completed. Total unique jobs found: {len(all_jobs)}")
            self.scraped_jobs = all_jobs
            return all_jobs
            
        except Exception as e:
            print(f"Error scraping job pages: {str(e)}")
            return all_jobs
    
    def _navigate_to_next_page(self):
        """
        Navigate to the next page of results
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            driver = self.webdriver_manager.get_driver()
            current_url = driver.current_url
            
            # Look for next page button with multiple strategies
            next_button_selectors = [
                'button[aria-label="Next"]',
                'button[aria-label*="next"]',
                '.artdeco-pagination__button--next',
                'a[aria-label="Next"]',
                'a[aria-label*="next"]',
                'button[data-test-pagination-page-btn="next"]',
                '.jobs-search-pagination__button--next',
                'li.artdeco-pagination__indicator--number + li button'
            ]
            
            next_button = None
            for selector in next_button_selectors:
                elements = self.webdriver_manager.find_elements_safe(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Check if button is actually clickable (not disabled)
                            classes = element.get_attribute('class') or ''
                            if 'disabled' not in classes.lower():
                                next_button = element
                                break
                    except:
                        continue
                if next_button:
                    break
            
            if not next_button:
                print("Next page button not found or disabled")
                return False
            
            # Scroll to button to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            # Click next button
            try:
                next_button.click()
            except ElementNotInteractableException:
                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", next_button)
            
            # Wait for new page to load
            time.sleep(4)
            
            # Verify we're on a new page by checking URL change
            new_url = driver.current_url
            if new_url != current_url:
                print(f"Successfully navigated to next page: {new_url}")
                return True
            else:
                print("URL did not change, pagination may have failed")
                return False
            
        except Exception as e:
            print(f"Error navigating to next page: {str(e)}")
            return False
    
    def get_scraped_jobs(self):
        """
        Get the list of scraped jobs
        
        Returns:
            list: List of job dictionaries
        """
        return self.scraped_jobs.copy()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.webdriver_manager.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()