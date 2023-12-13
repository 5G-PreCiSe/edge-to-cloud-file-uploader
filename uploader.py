from minio import Minio
from minio.error import S3Error
import os
import queue
import logging
import time
import threading

class S3Uploader:
    
    JOB_COMPLETED = 0
    JOB_MANUALLY_CANCELED = 1
    JOB_SHUTDOWN_CANCELED = 2
    JOB_EXCEPTION_CANCELED = 3
    
    def __init__(self,access_key, secret_key,s3_uri = "s3.5g-precise.de"):
        self.client = Minio(s3_uri,access_key=access_key,secret_key=secret_key,secure=False)
        self.queue = queue.Queue(100)
        
        self.cancellations = set()
        self._cancellation_lock = threading.Lock()
        
        self.update_callback = None
        self.status_callback = None
        
    def add_job(self, job):
        self.queue.put(job)
        
    def add_cancellation_flag(self, jobId):
        with self._cancellation_lock:
            if not jobId in self.cancellations:
                self.cancellations.add(jobId)
    
    def remove_cancellation_flag(self, jobId):
        with self._cancellation_lock:
            self.cancellations.discard(jobId)
    
    def has_cancellation_flag(self, jobId):
        with self._cancellation_lock:
            return jobId in self.cancellations
        
    def set_update_callback(self, fct):
        self.update_callback = fct
        
    def set_status_callback(self, fct):
        self.status_callback = fct
        
    def upload(self,job,cancel_event):
        try:
            jobId = job["jobId"]
            bucket = job["bucket"]
            path = job["path"]
            
            found = self.client.bucket_exists(bucket)
            if not found:
                self.client.make_bucket(bucket)
            
            dir = os.listdir(job["path"]) 
            for i, file in enumerate(dir):
                if not cancel_event.is_set():
                    if not self.has_cancellation_flag(jobId):
                        logging.info("Upload "+os.path.join(path,file))
                        self.client.fput_object(bucket,file,os.path.join(path,file))
                        if self.update_callback:
                            self.update_callback(len(dir),i+1)
                    else:
                        logging.info("Job '"+str(jobId)+"' manually canceled.")
                        if self.status_callback: 
                            self.status_callback(self.JOB_MANUALLY_CANCELED)
                        return 
                else:
                    logging.info("Job '"+str(jobId)+"' canceled due to shutdown.")
                    if self.status_callback: 
                        self.status_callback(self.JOB_SHUTDOWN_CANCELED)
                    return 
                if self.status_callback: 
                    self.status_callback(self.JOB_COMPLETED)
        except Exception as exc:
            logging.info("Job '"+str(jobId)+"' ended with exception '"+str(type(exc))+"'") 
            self.status_callback(self.JOB_EXCEPTION_CANCELED)
            
    def upload_worker(self, cancel_event):
        while not cancel_event.is_set():
            if not self.queue.empty():
                job = self.queue.get()
                logging.info("Job '"+str(job["jobId"])+"' loaded") 
                self.upload(job,cancel_event)
            time.sleep(0.5)
    
    
        
                
        
                
        
        
        
