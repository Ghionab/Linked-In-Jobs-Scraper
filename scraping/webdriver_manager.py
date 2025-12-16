"""
Selenium WebDriver Manager
Handles Chrome WebDriver configuration, initialization, and cleanup
"""

import random
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    InvalidSessionIdException
)
from webdriver_manager.chrome import ChromeDriverManager
import config


class WebDriverManager:
    """Manages Chrome WebDriver configuration and lifecycle"""
    
    def __init__(self, headless=True):
        """
        Initialize WebDriver manager
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.driver = None
        self.headless = headless
        self.wait = None
        self.last_request_time = None
        self.request_count = 0
        self.session_start_time = datetime.now()
        self.max_requests_per_session = 100  # Limit requests per session
        
    def setup_driver(self):
        """
        Configure and initialize Chrome WebDriver with appropriate options
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
            
        Raises:
            WebDriverException: If driver setup fails
        """
        try:
            # Configure Chrome options
            chrome_options = Options()
            
            # Basic options
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Performance and stability options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            
            # Window size for consistent rendering
            chrome_options.add_argument('--window-size=1920,1080')
            
            # User agent configuration
            user_agent = random.choice(config.USER_AGENTS)
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Additional privacy and security options
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set up Chrome service with automatic driver management
            service = Service(ChromeDriverManager().install())
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configure timeouts
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(10)
            
            # Set up WebDriverWait
            self.wait = WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT)
            
            # Execute script to hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return self.driver
            
        except Exception as e:
            raise WebDriverException(f"Failed to setup Chrome WebDriver: {str(e)}")
    
    def get_driver(self):
        """
        Get the current WebDriver instance, initializing if necessary
        
        Returns:
            webdriver.Chrome: Chrome WebDriver instance
        """
        if self.driver is None:
            self.setup_driver()
        return self.driver
    
    def get_wait(self):
        """
        Get WebDriverWait instance
        
        Returns:
            WebDriverWait: WebDriverWait instance for explicit waits
        """
        if self.wait is None and self.driver is not None:
            self.wait = WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT)
        return self.wait
    
    def navigate_to_url(self, url):
        """
        Navigate to specified URL with basic error handling
        For retry logic, use navigate_to_url_with_retry()
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.apply_request_delay()
            
            driver = self.get_driver()
            driver.get(url)
            
            # Wait for page to load
            if self.wait_for_page_load():
                return True
            else:
                return False
            
        except TimeoutException:
            print(f"Timeout while loading URL: {url}")
            return False
        except Exception as e:
            print(f"Error navigating to URL {url}: {str(e)}")
            return False
    
    def wait_for_page_load(self):
        """
        Wait for page to fully load
        
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        try:
            wait = self.get_wait()
            # Wait for document ready state
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            return True
        except TimeoutException:
            print("Timeout waiting for page to load")
            return False
    
    def wait_for_element(self, by, value, timeout=None):
        """
        Wait for element to be present and visible
        For retry logic with stale element handling, use wait_for_element_with_retry()
        
        Args:
            by: Selenium By locator type
            value (str): Locator value
            timeout (int): Optional timeout override
            
        Returns:
            WebElement or None: Found element or None if not found
        """
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
            else:
                wait = self.get_wait()
                
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
            
        except TimeoutException:
            print(f"Element not found: {by}={value}")
            return None
        except Exception as e:
            print(f"Error waiting for element {by}={value}: {str(e)}")
            return None
    
    def find_elements_safe(self, by, value):
        """
        Safely find elements without throwing exceptions
        
        Args:
            by: Selenium By locator type
            value (str): Locator value
            
        Returns:
            list: List of found elements (empty if none found)
        """
        try:
            driver = self.get_driver()
            return driver.find_elements(by, value)
        except NoSuchElementException:
            return []
        except Exception as e:
            print(f"Error finding elements {by}={value}: {str(e)}")
            return []
    
    def get_page_source(self):
        """
        Get current page source
        
        Returns:
            str: Page source HTML or empty string if error
        """
        try:
            driver = self.get_driver()
            return driver.page_source
        except Exception as e:
            print(f"Error getting page source: {str(e)}")
            return ""
    
    def cleanup(self):
        """
        Clean up WebDriver resources
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error during driver cleanup: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
    def apply_request_delay(self):
        """
        Apply delay between requests to avoid being blocked
        Implements intelligent delay based on request frequency
        """
        current_time = datetime.now()
        
        # Calculate delay based on configuration
        base_delay = config.DEFAULT_REQUEST_DELAY
        max_delay = config.MAX_REQUEST_DELAY
        
        # Add randomization to make requests less predictable
        delay = random.uniform(base_delay, max_delay)
        
        # Increase delay if making too many requests
        if self.request_count > 20:
            delay *= 1.5  # 50% longer delay after 20 requests
        if self.request_count > 50:
            delay *= 2.0  # Double delay after 50 requests
        
        # Ensure minimum time between requests
        if self.last_request_time:
            time_since_last = (current_time - self.last_request_time).total_seconds()
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                print(f"Applying delay: {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def navigate_to_url_with_retry(self, url, max_retries=None):
        """
        Navigate to URL with retry logic and delay mechanisms
        
        Args:
            url (str): URL to navigate to
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        if max_retries is None:
            max_retries = config.MAX_RETRY_ATTEMPTS
        
        for attempt in range(max_retries + 1):
            try:
                # Apply delay before request
                if attempt > 0:
                    # Exponential backoff for retries
                    retry_delay = (2 ** attempt) * config.DEFAULT_REQUEST_DELAY
                    print(f"Retry attempt {attempt}, waiting {retry_delay:.2f} seconds")
                    time.sleep(retry_delay)
                else:
                    self.apply_request_delay()
                
                # Check if we've exceeded session limits
                if self._should_refresh_session():
                    print("Refreshing session due to limits")
                    self._refresh_session()
                
                driver = self.get_driver()
                driver.get(url)
                
                # Wait for page to load
                if self.wait_for_page_load():
                    print(f"Successfully loaded: {url}")
                    return True
                else:
                    raise TimeoutException("Page load timeout")
                    
            except TimeoutException as e:
                print(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    print(f"Failed to load URL after {max_retries + 1} attempts: {url}")
                    return False
                    
            except InvalidSessionIdException:
                print("Invalid session, recreating driver")
                self._refresh_session()
                if attempt == max_retries:
                    return False
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    print(f"Failed to load URL after {max_retries + 1} attempts: {url}")
                    return False
        
        return False
    
    def wait_for_element_with_retry(self, by, value, timeout=None, max_retries=3):
        """
        Wait for element with retry logic for stale elements
        
        Args:
            by: Selenium By locator type
            value (str): Locator value
            timeout (int): Optional timeout override
            max_retries (int): Maximum retry attempts for stale elements
            
        Returns:
            WebElement or None: Found element or None if not found
        """
        for attempt in range(max_retries + 1):
            try:
                if timeout:
                    wait = WebDriverWait(self.driver, timeout)
                else:
                    wait = self.get_wait()
                    
                element = wait.until(EC.presence_of_element_located((by, value)))
                
                # Verify element is still valid
                element.is_displayed()  # This will raise StaleElementReferenceException if stale
                return element
                
            except StaleElementReferenceException:
                print(f"Stale element on attempt {attempt + 1}, retrying...")
                if attempt == max_retries:
                    print(f"Element remained stale after {max_retries + 1} attempts: {by}={value}")
                    return None
                time.sleep(1)  # Brief pause before retry
                
            except TimeoutException:
                print(f"Element not found: {by}={value}")
                return None
            except Exception as e:
                print(f"Error finding element {by}={value}: {str(e)}")
                return None
        
        return None
    
    def handle_rate_limiting(self, response_code=None, error_message=""):
        """
        Handle rate limiting and blocking scenarios
        
        Args:
            response_code (int): HTTP response code if available
            error_message (str): Error message from exception
        """
        print("Rate limiting detected, implementing countermeasures...")
        
        # Implement progressive delays
        if "rate limit" in error_message.lower() or response_code == 429:
            delay = random.uniform(30, 60)  # 30-60 second delay
            print(f"Rate limited, waiting {delay:.2f} seconds")
            time.sleep(delay)
            
        elif "blocked" in error_message.lower() or response_code == 403:
            delay = random.uniform(60, 120)  # 1-2 minute delay
            print(f"Access blocked, waiting {delay:.2f} seconds")
            time.sleep(delay)
            
        # Refresh session to get new user agent and clear cookies
        self._refresh_session()
    
    def _should_refresh_session(self):
        """
        Determine if session should be refreshed based on usage patterns
        
        Returns:
            bool: True if session should be refreshed
        """
        # Refresh after too many requests
        if self.request_count >= self.max_requests_per_session:
            return True
            
        # Refresh after long session duration (1 hour)
        session_duration = datetime.now() - self.session_start_time
        if session_duration > timedelta(hours=1):
            return True
            
        return False
    
    def _refresh_session(self):
        """
        Refresh the browser session with new configuration
        """
        try:
            print("Refreshing browser session...")
            
            # Clean up current session
            if self.driver:
                self.driver.quit()
                
            # Reset counters
            self.request_count = 0
            self.session_start_time = datetime.now()
            self.last_request_time = None
            
            # Create new driver instance
            self.driver = None
            self.wait = None
            self.setup_driver()
            
            print("Session refreshed successfully")
            
        except Exception as e:
            print(f"Error refreshing session: {str(e)}")
    
    def handle_connection_error(self, error):
        """
        Handle various connection errors with appropriate responses
        
        Args:
            error: Exception object
            
        Returns:
            bool: True if error was handled and retry should be attempted
        """
        error_message = str(error).lower()
        
        if "connection refused" in error_message:
            print("Connection refused, waiting before retry...")
            time.sleep(random.uniform(10, 20))
            return True
            
        elif "timeout" in error_message:
            print("Connection timeout, implementing delay...")
            time.sleep(random.uniform(5, 15))
            return True
            
        elif "network" in error_message:
            print("Network error detected, waiting...")
            time.sleep(random.uniform(15, 30))
            return True
            
        elif "ssl" in error_message or "certificate" in error_message:
            print("SSL/Certificate error, refreshing session...")
            self._refresh_session()
            return True
            
        else:
            print(f"Unhandled connection error: {error_message}")
            return False
    
    def get_page_source_safe(self):
        """
        Safely get page source with error handling
        
        Returns:
            str: Page source HTML or empty string if error
        """
        try:
            driver = self.get_driver()
            
            # Verify driver is still valid
            driver.current_url  # This will raise exception if session is invalid
            
            return driver.page_source
            
        except InvalidSessionIdException:
            print("Invalid session while getting page source, refreshing...")
            self._refresh_session()
            return ""
            
        except Exception as e:
            print(f"Error getting page source: {str(e)}")
            return ""
    
    def is_blocked_or_captcha(self, page_source=""):
        """
        Check if the current page indicates blocking or CAPTCHA
        
        Args:
            page_source (str): Page source to check (optional)
            
        Returns:
            bool: True if blocking/CAPTCHA detected
        """
        if not page_source:
            page_source = self.get_page_source_safe()
        
        if not page_source:
            return False
        
        page_source_lower = page_source.lower()
        
        # Check for common blocking indicators
        blocking_indicators = [
            "captcha",
            "blocked",
            "rate limit",
            "too many requests",
            "access denied",
            "forbidden",
            "security check",
            "unusual activity"
        ]
        
        for indicator in blocking_indicators:
            if indicator in page_source_lower:
                print(f"Blocking detected: {indicator}")
                return True
        
        return False