import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class LinkedInHTMLParser:
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
    
    def parse_job_listings(self, html_content):
        jobs = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', {'data-entity-urn': True}) or \
                       soup.find_all('li', class_=lambda x: x and 'job' in x.lower()) or \
                       soup.select('.job-search-card')
            
            for card in job_cards:
                job = self._extract_job_data(card)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"Error parsing jobs: {e}")
            
        return jobs
    
    def _extract_job_data(self, card):
        try:
            # Extract basic info
            title_elem = card.find('h3') or card.find('a', href=lambda x: x and '/jobs/view/' in x)
            company_elem = card.find('h4') or card.find('a', href=lambda x: x and '/company/' in x)
            
            if not title_elem or not company_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            
            # Extract other fields
            location = self._find_location(card)
            posted_date = self._find_posted_date(card)
            url = self._find_job_url(card)
            
            return {
                'id': str(hash(f"{title}_{company}") % 1000000),
                'title': title,
                'company': company,
                'location': location,
                'posted_date': posted_date,
                'description': '',
                'url': url,
                'job_type': '',
                'experience_level': '',
                'status': 'Not Reviewed',
                'scraped_at': datetime.now()
            }
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    def _find_location(self, card):
        # Look for location text
        for elem in card.find_all(['span', 'div']):
            text = elem.get_text(strip=True)
            if text and any(word in text.lower() for word in ['remote', 'hybrid']) or \
               (',' in text and len(text) < 50 and not any(word in text.lower() for word in ['ago', 'day', 'week'])):
                return text
        return ""
    
    def _find_posted_date(self, card):
        # Look for time elements or "ago" text
        time_elem = card.find('time')
        if time_elem:
            return time_elem.get('datetime', time_elem.get_text(strip=True))
            
        for elem in card.find_all(['span', 'div']):
            text = elem.get_text(strip=True)
            if 'ago' in text.lower():
                return text
        return ""
    
    def _find_job_url(self, card):
        # Find job link
        link = card.find('a', href=lambda x: x and '/jobs/view/' in x)
        if link:
            href = link['href']
            if href.startswith('/'):
                return f"{self.base_url}{href}"
            return href
        return ""