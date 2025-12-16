"""
Job Data Manager
Manages in-memory job data and status tracking for the LinkedIn Job Scraper
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


class JobDataManager:
    """Manages in-memory job data and status tracking"""
    
    def __init__(self):
        """Initialize the job data manager"""
        self.jobs_data: Dict[str, Dict[str, Any]] = {}
        self.status_options = [
            "Not Reviewed",
            "Interested", 
            "Applied",
            "Not Interested"
        ]
        
    def add_jobs(self, jobs_list: List[Dict[str, Any]]) -> None:
        """Add new jobs to the dataset"""
        for job_data in jobs_list:
            job_id = job_data.get('id')
            if job_id:
                # Ensure job has all required fields
                job_data.setdefault('status', 'Not Reviewed')
                job_data.setdefault('scraped_at', datetime.now())
                self.jobs_data[job_id] = job_data.copy()
                
    def add_job(self, job_data: Dict[str, Any]) -> str:
        """Add a single job to the dataset and return its ID"""
        job_id = job_data.get('id')
        if not job_id:
            # Generate ID if not provided
            job_id = f"job_{len(self.jobs_data) + 1}_{int(datetime.now().timestamp())}"
            job_data['id'] = job_id
            
        # Ensure job has all required fields
        job_data.setdefault('status', 'Not Reviewed')
        job_data.setdefault('scraped_at', datetime.now())
        
        self.jobs_data[job_id] = job_data.copy()
        return job_id
        
    def update_job_status(self, job_id: str, new_status: str) -> bool:
        """Update the status of a specific job"""
        if job_id in self.jobs_data and new_status in self.status_options:
            self.jobs_data[job_id]['status'] = new_status
            self.jobs_data[job_id]['status_updated_at'] = datetime.now()
            return True
        return False
        
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        return self.jobs_data.get(job_id)
        
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs data"""
        return list(self.jobs_data.values())
        
    def get_filtered_jobs(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get jobs filtered by specified criteria"""
        filtered_jobs = []
        
        for job in self.jobs_data.values():
            # Apply filters
            if filters.get('status') and job.get('status') != filters['status']:
                continue
            if filters.get('job_type') and job.get('job_type') != filters['job_type']:
                continue
            if filters.get('experience_level') and job.get('experience_level') != filters['experience_level']:
                continue
            if filters.get('company') and filters['company'].lower() not in job.get('company', '').lower():
                continue
            if filters.get('location') and filters['location'].lower() not in job.get('location', '').lower():
                continue
                
            filtered_jobs.append(job)
            
        return filtered_jobs
        
    def search_jobs(self, search_term: str) -> List[Dict[str, Any]]:
        """Search jobs by title, company, or description"""
        if not search_term:
            return self.get_all_jobs()
            
        search_term = search_term.lower()
        matching_jobs = []
        
        for job in self.jobs_data.values():
            # Search in title, company, and description
            if (search_term in job.get('title', '').lower() or
                search_term in job.get('company', '').lower() or
                search_term in job.get('description', '').lower()):
                matching_jobs.append(job)
                
        return matching_jobs
        
    def get_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all jobs with a specific status"""
        return [job for job in self.jobs_data.values() if job.get('status') == status]
        
    def get_status_counts(self) -> Dict[str, int]:
        """Get count of jobs by status"""
        counts = {status: 0 for status in self.status_options}
        
        for job in self.jobs_data.values():
            status = job.get('status', 'Not Reviewed')
            if status in counts:
                counts[status] += 1
                
        return counts
        
    def clear_data(self) -> None:
        """Clear all stored job data"""
        self.jobs_data.clear()
        
    def get_job_count(self) -> int:
        """Get total number of jobs"""
        return len(self.jobs_data)
        
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the dataset"""
        if job_id in self.jobs_data:
            del self.jobs_data[job_id]
            return True
        return False
        
    def get_jobs_for_export(self) -> List[Dict[str, Any]]:
        """Get all jobs data formatted for CSV export"""
        export_jobs = []
        
        for job in self.jobs_data.values():
            # Create a copy with formatted data for export
            export_job = job.copy()
            
            # Format datetime fields for export
            if 'scraped_at' in export_job and isinstance(export_job['scraped_at'], datetime):
                export_job['scraped_at'] = export_job['scraped_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'status_updated_at' in export_job and isinstance(export_job['status_updated_at'], datetime):
                export_job['status_updated_at'] = export_job['status_updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
            export_jobs.append(export_job)
            
        return export_jobs