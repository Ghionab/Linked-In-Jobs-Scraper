from datetime import datetime

class JobDataManager:
    def __init__(self):
        self.jobs = {}
        self.status_options = ["Not Reviewed", "Interested", "Applied", "Not Interested"]
        
    def add_jobs(self, jobs_list):
        for job in jobs_list:
            job_id = job.get('id', str(len(self.jobs)))
            job['status'] = job.get('status', 'Not Reviewed')
            job['scraped_at'] = datetime.now()
            self.jobs[job_id] = job
            
    def add_job(self, job_data):
        job_id = job_data.get('id', str(len(self.jobs)))
        job_data['status'] = job_data.get('status', 'Not Reviewed')
        job_data['scraped_at'] = datetime.now()
        self.jobs[job_id] = job_data
        return job_id
        
    def update_job_status(self, job_id, status):
        if job_id in self.jobs and status in self.status_options:
            self.jobs[job_id]['status'] = status
            return True
        return False
        
    def get_job(self, job_id):
        return self.jobs.get(job_id)
        
    def get_all_jobs(self):
        return list(self.jobs.values())
        
    def get_job_count(self):
        return len(self.jobs)
        
    def clear_jobs(self):
        self.jobs.clear()