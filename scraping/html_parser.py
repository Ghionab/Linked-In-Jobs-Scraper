"""
HTML Parser for LinkedIn Job Listings
BeautifulSoup-based parser for extracting job data from LinkedIn pages
"""

import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import config


class LinkedInHTMLParser:
    """Parser for LinkedIn job listing HTML content"""
    
    def __init__(self):
        """Initialize the HTML parser"""
        self.base_url = "https://www.linkedin.com"
    
    def parse_job_listings(self, html_content):
        """
        Parse job listings from LinkedIn search results page
        
        Args:
            html_content (str): HTML content from LinkedIn jobs page
            
        Returns:
            list: List of job dictionaries with extracted data
        """
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find job cards - LinkedIn uses various selectors for job listings
            job_cards = self._find_job_cards(soup)
            
            for card in job_cards:
                job_data = self._extract_job_data(card)
                if job_data:
                    jobs.append(job_data)
                    
        except Exception as e:
            print(f"Error parsing job listings: {str(e)}")
            
        return jobs
    
    def _find_job_cards(self, soup):
        """
        Find job card elements in the parsed HTML
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of job card elements
        """
        # LinkedIn job cards can have different selectors depending on page layout
        selectors = [
            'div[data-entity-urn*="job"]',  # Main job card selector
            '.job-search-card',             # Alternative selector
            '.jobs-search__results-list li', # List item selector
            '.scaffold-layout__list-container li',  # Another layout selector
            '.jobs-search-results-list__list-item',  # Updated LinkedIn selector
            '.job-result-card',             # Job result card
            'li[data-occludable-job-id]',   # Job list items with ID
            '.base-search-card',            # Base search card
            'article.job-search-card'       # Article-based job cards
        ]
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                print(f"Found {len(cards)} job cards using selector: {selector}")
                return cards
        
        # If no cards found with specific selectors, try broader search
        print("No job cards found with specific selectors, trying broader search...")
        
        # Look for any elements that might contain job information
        potential_cards = []
        
        # Search for elements with job-related attributes or classes
        job_elements = soup.find_all(['div', 'li', 'article'], attrs={
            'class': lambda x: x and any(term in ' '.join(x) for term in ['job', 'card', 'result'])
        })
        
        for element in job_elements:
            # Check if element contains typical job information
            if (element.find('a', href=True) and 
                (element.find(string=lambda text: text and any(word in text.lower() for word in ['ago', 'day', 'week', 'month'])) or
                 element.find(['h3', 'h4', 'h5']))):
                potential_cards.append(element)
        
        if potential_cards:
            print(f"Found {len(potential_cards)} potential job cards using broader search")
            return potential_cards[:20]  # Limit to first 20 to avoid noise
                
        return []
    
    def _extract_job_data(self, card):
        """
        Extract job information from a single job card
        
        Args:
            card: BeautifulSoup element representing a job card
            
        Returns:
            dict: Job data dictionary or None if extraction fails
        """
        try:
            job_data = {
                'id': self._generate_job_id(card),
                'title': self._extract_job_title(card),
                'company': self._extract_company_name(card),
                'location': self._extract_location(card),
                'posted_date': self._extract_posted_date(card),
                'description': self._extract_description(card),
                'url': self._extract_job_url(card),
                'job_type': self._extract_job_type(card),
                'experience_level': self._extract_experience_level(card),
                'status': 'Not Reviewed',
                'scraped_at': datetime.now()
            }
            
            # Validate that we have minimum required data
            if job_data['title'] and job_data['company']:
                # Clean up empty fields
                for key, value in job_data.items():
                    if isinstance(value, str) and not value.strip():
                        job_data[key] = ""
                
                # Ensure URL is properly formatted
                if job_data['url'] and not job_data['url'].startswith('http'):
                    job_data['url'] = urljoin(self.base_url, job_data['url'])
                
                # Ensure we have a valid job ID
                if not job_data['id']:
                    job_data['id'] = self._generate_fallback_id(job_data)
                
                return job_data
            else:
                # Log what data we were able to extract for debugging
                extracted_fields = {k: v for k, v in job_data.items() if v and k not in ['scraped_at']}
                print(f"Insufficient job data extracted: {extracted_fields}")
                
        except Exception as e:
            print(f"Error extracting job data from card: {str(e)}")
            
        return None
    
    def _generate_fallback_id(self, job_data):
        """Generate a fallback ID when no ID can be extracted from the card"""
        # Create ID from title and company
        title = job_data.get('title', '')
        company = job_data.get('company', '')
        location = job_data.get('location', '')
        
        # Create a hash from the combination
        id_string = f"{title}_{company}_{location}".lower().replace(' ', '_')
        return str(hash(id_string) % 1000000)  # Keep it reasonably short
    
    def _generate_job_id(self, card):
        """Generate unique job ID from card attributes"""
        # Try to extract LinkedIn job ID from data attributes
        job_id = card.get('data-entity-urn', '')
        if 'job:' in job_id:
            return job_id.split('job:')[-1]
        
        # Fallback: generate ID from job URL or other attributes
        job_link = card.find('a', href=True)
        if job_link and 'jobs/view/' in job_link['href']:
            return job_link['href'].split('jobs/view/')[-1].split('?')[0]
            
        # Last resort: use hash of card content
        return str(hash(str(card)[:100]))
    
    def _extract_job_title(self, card):
        """Extract job title from card"""
        selectors = [
            'h3 a span[title]',
            'h3 a span',
            '.job-search-card__title a',
            'h4 a',
            'a[data-control-name="job_search_job_title"] span',
            '.base-search-card__title a',
            '.job-result-card__title a',
            'h3.base-search-card__title a',
            'a[data-tracking-control-name*="job_title"]',
            '.job-search-card__title-link',
            'h3 a[href*="/jobs/view/"]',
            'h4 a[href*="/jobs/view/"]',
            '.sr-only + span',  # Sometimes title is after screen reader text
            'a[aria-label*="job"]'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                title = element.get('title') or element.get('aria-label') or element.get_text(strip=True)
                if title and len(title.strip()) > 0:
                    # Clean up common prefixes/suffixes
                    title = title.replace('View job details for ', '').replace(' job', '')
                    return self._clean_text(title)
        
        # Fallback: look for any link that might be a job title
        job_links = card.find_all('a', href=True)
        for link in job_links:
            if '/jobs/view/' in link.get('href', ''):
                title_text = link.get_text(strip=True)
                if title_text and len(title_text) > 5:  # Reasonable title length
                    return self._clean_text(title_text)
        
        return ""
    
    def _extract_company_name(self, card):
        """Extract company name from card"""
        selectors = [
            'h4 a span[title]',
            'h4 a span',
            '.job-search-card__subtitle a',
            'a[data-control-name="job_search_company_name"] span',
            '.job-search-card__subtitle-link',
            '.base-search-card__subtitle a',
            '.job-result-card__subtitle a',
            'h4.base-search-card__subtitle a',
            'a[data-tracking-control-name*="company"]',
            '.job-search-card__subtitle',
            'h4 a[href*="/company/"]',
            '.artdeco-entity-lockup__subtitle a',
            '.job-search-card__company-name'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                company = element.get('title') or element.get('aria-label') or element.get_text(strip=True)
                if company and len(company.strip()) > 0:
                    return self._clean_text(company)
        
        # Fallback: look for company links
        company_links = card.find_all('a', href=True)
        for link in company_links:
            if '/company/' in link.get('href', ''):
                company_text = link.get_text(strip=True)
                if company_text and len(company_text) > 1:
                    return self._clean_text(company_text)
        
        # Last resort: look for h4 elements that might contain company names
        h4_elements = card.find_all('h4')
        for h4 in h4_elements:
            text = h4.get_text(strip=True)
            if text and len(text) > 1 and len(text) < 100:  # Reasonable company name length
                return self._clean_text(text)
        
        return ""
    
    def _extract_location(self, card):
        """Extract job location from card"""
        selectors = [
            '.job-search-card__location',
            'span[data-test="job-search-card-location"]',
            '.job-result-card__location',
            '.base-search-card__metadata span',
            '.job-search-card__metadata span',
            '.artdeco-entity-lockup__metadata span',
            'div[data-test-id*="location"]',
            '.job-search-card__location-text'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                location = element.get_text(strip=True)
                if location and len(location.strip()) > 0:
                    # Filter out non-location text
                    if not any(word in location.lower() for word in ['ago', 'day', 'week', 'month', 'hour', 'applicant', 'easy apply']):
                        return self._clean_text(location)
        
        # Fallback: look for location patterns in metadata
        metadata_elements = card.find_all(['span', 'div'], class_=lambda x: x and 'metadata' in ' '.join(x))
        for element in metadata_elements:
            text = element.get_text(strip=True)
            # Look for location patterns (city, state abbreviations, country codes)
            if text and any(pattern in text for pattern in [', ', ' - ', 'Remote', 'Hybrid']):
                if not any(word in text.lower() for word in ['ago', 'day', 'week', 'month', 'hour', 'applicant']):
                    return self._clean_text(text)
        
        return ""
    
    def _extract_posted_date(self, card):
        """Extract job posting date from card"""
        selectors = [
            'time',
            '.job-search-card__listdate',
            'span[data-test="job-search-card-listdate"]',
            '.base-search-card__metadata time',
            '.job-result-card__listdate',
            '.artdeco-entity-lockup__metadata time'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                date_text = element.get('datetime') or element.get('title') or element.get_text(strip=True)
                if date_text:
                    return self._parse_posted_date(date_text)
        
        # Fallback: look for date patterns in text
        all_text = card.get_text()
        date_patterns = [
            r'(\d+)\s+(day|days|week|weeks|month|months)\s+ago',
            r'(today|yesterday)',
            r'(\d+)\s+(hour|hours|minute|minutes)\s+ago'
        ]
        
        import re
        for pattern in date_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return self._parse_posted_date(match.group(0))
        
        return ""
    
    def _extract_description(self, card):
        """Extract job description preview from card"""
        selectors = [
            '.job-search-card__snippet',
            'p[data-test="job-search-card-snippet"]',
            '.job-result-card__snippet',
            '.base-search-card__snippet',
            '.job-search-card__description',
            '.artdeco-entity-lockup__content p',
            '.job-search-card__summary'
        ]
        
        for selector in selectors:
            element = card.select_one(selector)
            if element:
                description = element.get_text(strip=True)
                if description and len(description) > 10:  # Ensure meaningful description
                    return self._clean_text(description)
        
        # Fallback: look for paragraph elements that might contain descriptions
        paragraphs = card.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20 and len(text) < 500:  # Reasonable description length
                # Avoid metadata text
                if not any(word in text.lower() for word in ['ago', 'applicant', 'easy apply', 'promoted']):
                    return self._clean_text(text)
        
        return ""
    
    def _extract_job_url(self, card):
        """Extract LinkedIn job URL from card"""
        # Look for job-specific links first
        job_link_selectors = [
            'a[href*="/jobs/view/"]',
            'h3 a[href]',
            'h4 a[href]',
            '.job-search-card__title a',
            '.base-search-card__title a'
        ]
        
        for selector in job_link_selectors:
            link = card.select_one(selector)
            if link and link.get('href'):
                href = link['href']
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                elif 'linkedin.com' in href:
                    return href
        
        # Fallback: look for any job-related link
        all_links = card.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            if '/jobs/view/' in href:
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                elif 'linkedin.com' in href:
                    return href
        
        return ""
    
    def _extract_job_type(self, card):
        """Extract job type from card (if available)"""
        # Job type is often not directly available in search results
        # This would typically be extracted from the full job page
        return ""
    
    def _extract_experience_level(self, card):
        """Extract experience level from card (if available)"""
        # Experience level is often not directly available in search results
        # This would typically be extracted from the full job page
        return ""
    
    def _clean_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        return text
    
    def _parse_posted_date(self, date_text):
        """Parse posted date text into standardized format"""
        if not date_text:
            return ""
        
        date_text = date_text.lower().strip()
        
        try:
            # Handle relative dates like "2 days ago", "1 week ago"
            if 'ago' in date_text:
                if 'hour' in date_text or 'minute' in date_text:
                    return "Today"
                elif 'day' in date_text:
                    days = re.search(r'(\d+)', date_text)
                    if days:
                        days_ago = int(days.group(1))
                        date = datetime.now() - timedelta(days=days_ago)
                        return date.strftime("%Y-%m-%d")
                elif 'week' in date_text:
                    weeks = re.search(r'(\d+)', date_text)
                    if weeks:
                        weeks_ago = int(weeks.group(1))
                        date = datetime.now() - timedelta(weeks=weeks_ago)
                        return date.strftime("%Y-%m-%d")
                elif 'month' in date_text:
                    return "1+ months ago"
            
            # Handle "today", "yesterday"
            if 'today' in date_text:
                return datetime.now().strftime("%Y-%m-%d")
            elif 'yesterday' in date_text:
                date = datetime.now() - timedelta(days=1)
                return date.strftime("%Y-%m-%d")
            
            # If it's already a formatted date, return as is
            return date_text
            
        except Exception:
            return date_text
    
    def parse_job_details(self, html_content):
        """
        Parse detailed job information from individual job page
        
        Args:
            html_content (str): HTML content from individual LinkedIn job page
            
        Returns:
            dict: Detailed job information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            details = {
                'full_description': self._extract_full_description(soup),
                'job_type': self._extract_job_type_from_details(soup),
                'experience_level': self._extract_experience_from_details(soup),
                'company_info': self._extract_company_info(soup),
                'requirements': self._extract_requirements(soup)
            }
            
            return details
            
        except Exception as e:
            print(f"Error parsing job details: {str(e)}")
            return {}
    
    def _extract_full_description(self, soup):
        """Extract full job description from job details page"""
        selectors = [
            '.show-more-less-html__markup',
            '.jobs-description__content',
            '.jobs-box__html-content'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get text content and preserve some formatting
                description = element.get_text(separator='\n', strip=True)
                return self._clean_text(description)
        
        return ""
    
    def _extract_job_type_from_details(self, soup):
        """Extract job type from job details page"""
        # Look for job criteria section
        criteria_items = soup.select('.jobs-unified-top-card__job-insight span')
        
        for item in criteria_items:
            text = item.get_text(strip=True).lower()
            if any(job_type in text for job_type in ['full-time', 'part-time', 'contract', 'internship']):
                return text.title()
        
        return ""
    
    def _extract_experience_from_details(self, soup):
        """Extract experience level from job details page"""
        # Look for seniority level in job criteria
        criteria_items = soup.select('.jobs-unified-top-card__job-insight span')
        
        for item in criteria_items:
            text = item.get_text(strip=True).lower()
            if any(level in text for level in ['entry', 'mid', 'senior', 'executive', 'associate']):
                return text.title()
        
        return ""
    
    def _extract_company_info(self, soup):
        """Extract additional company information"""
        company_info = {}
        
        # Company size, industry, etc.
        company_insights = soup.select('.jobs-unified-top-card__company-name a')
        if company_insights:
            company_info['company_url'] = company_insights[0].get('href', '')
        
        return company_info
    
    def _extract_requirements(self, soup):
        """Extract job requirements and qualifications"""
        # This would extract specific requirements from the job description
        # Implementation depends on how LinkedIn structures this information
        return []
   