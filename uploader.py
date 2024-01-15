from minio import Minio
from minio.error import S3Error
import os
import queue
import logging
import time
import threading
from datetime import datetime
import uuid

from api import MissingArgumentException, UnknownCommandException, ApiException

class S3Uploader:
    
    JOB_COMPLETED = 0
    JOB_MANUALLY_CANCELED = 1
    JOB_SHUTDOWN_CANCELED = 2
    JOB_EXCEPTION_CANCELED = 3
    
    def __init__(self, configuration_handler):
        self.configuration = configuration_handler
        
        self.input_queue = queue.Queue(100)
        self.output_queue = queue.Queue(10000)
        self.error_queue = queue.Queue(10000)
        self.current_job = None
        
        self.cancellations = set()
        self._cancellation_lock = threading.Lock()
        
        self._current_job_lock = threading.Lock()
        
        self.update_callback = None
        self.status_callback = None
        
    def start(self,cancel_event, access_key, secret_key,s3_uri = "s3.5g-precise.de"):
        self.client = Minio(s3_uri,access_key=access_key,secret_key=secret_key,secure=False)
        
        self.upload_worker = threading.Thread(target=self.upload_worker,args=(cancel_event,),daemon=False)
        self.upload_worker_thread.start()
        
    def add_job(self, job):
        self.input_queue.put(job)
        
        
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
        
    def set_current_job(self, job):
        with self._current_job_lock:
            self.current_job = job
    
    def get_current_job(self):
        with self._current_job_lock:
            return self.current_job
    
    def remove_current_job(self):
        with self._current_job_lock:
            self.current_job = None
        
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
                        self.remove_current_job()
                        self.output_queue.put(job)
                        return 
                else:
                    logging.info("Job '"+str(jobId)+"' canceled due to shutdown.")
                    if self.status_callback: 
                        self.status_callback(self.JOB_SHUTDOWN_CANCELED)
                    self.remove_current_job()
                    self.error_queue.put(job)
                    return 
            if self.status_callback: 
                self.status_callback(self.JOB_COMPLETED)
            self.remove_current_job()
            self.output_queue.put(job)
        except Exception as exc:
            logging.error("Job '"+str(jobId)+"' ended with exception '"+str(type(exc))+"'") 
            logging.exception(exc)
            self.status_callback(self.JOB_EXCEPTION_CANCELED)
            self.remove_current_job()
            self.error_queue.put(job)
            
    def upload_worker(self, cancel_event):
        while not cancel_event.is_set():
            if not self.input_queue.empty():
                job = self.input_queue.get()
                self.set_current_job(job)
                logging.info("Job '"+str(job["jobId"])+"' loaded") 
                self.upload(job,cancel_event)
            time.sleep(0.5)
            
    def request(self, req_payload, topic):
        
        if "command" in req_payload:
            if req_payload["command"] == "create":
                response = self.cmd_add_job(req_payload)
            elif req_payload["command"] == "query":
                response = self.cmd_query_job(req_payload)
            elif req_payload["command"] == "cancel":
                response = self.cmd_cancel_job(req_payload)
            else:
                raise UnknownCommandException(command=req_payload["command"])
        else:
            raise MissingArgumentException(argument="command")

        response["command"] = req_payload["command"]
        return response

    def build_job_response(self, job, state):
        response = {
            "jobId": job["jobId"],
            "bucket": job["bucket"],
            "path": job["path"],
            "state": state,
            "requestTopic": self.configuration.get("api","RequestJobsTopic"),
            "requestTopic": self.configuration.get("api","ResponseJobsTopic")+"/"+job["jobId"].replace(" ","-").replace("#","-").replace("*","-")
        }
        return response

    def cmd_add_job(self, req_payload):
        if "path" in req_payload:
            path = req_payload["path"]
        else:
            raise MissingArgumentException("path")

        if "bucket" in req_payload:
            bucket = req_payload["bucket"]
        else:
            bucket = self.configuration.get("device","DeviceId")+"_"+datetime.now().strftime("%m-%d-%Y_%H:%M:%S")
            
        if "jobId" in req_payload:
            jobId = req_payload["jobId"]
        else:
            jobId = str(uuid.uuid4())
            
        job = {
            "jobId": jobId,
            "bucket": bucket,
            "path": path
        }
        self.add_job(job)
        return self.build_job_response(job,"scheduled")
    
    def cmd_query_job(self, req_payload):
        if "jobId" in req_payload:
            job_id = req_payload["jobId"]
        else:
            job_id = None
            
        if "state" in req_payload:
            state = req_payload["state"]
        else:
            state = None
            
        if not job_id:
            response = {
                "jobs": []
            }
        
        if state == "scheduled" or state == "canceled" or not state:
            for job in list(self.input_queue):
                if job_id 
                    if job["jobId"] == job_id:
                        if self.has_cancellation_flag(job_id):
                            return self.build_job_response(job,"canceled (scheduled)")
                        else:
                            return self.build_job_response(job,"scheduled")
                else:
                    if self.has_cancellation_flag(job_id):
                        response["jobs"].append(self.build_job_response(job,"canceled (scheduled)"))
                    else:
                        response["jobs"].append(self.build_job_response(job,"scheduled"))
        
        if state == "completed" or state == "canceled" or not state:
            for job in list(self.output_queue):
                if job_id 
                    if job["jobId"] == job_id:
                        if self.has_cancellation_flag(job_id):
                            return self.build_job_response(job,"canceled (completed)")
                        else:
                            return self.build_job_response(job,"completed")
                else:
                    if self.has_cancellation_flag(job_id):
                        response["jobs"].append(self.build_job_response(job,"canceled (completed)"))
                    else:
                        response["jobs"].append(self.build_job_response(job,"completed"))   
                     
        if state == "error" or state == "canceled" or not state:
            for job in list(self.error_queue):
                if job_id 
                    if job["jobId"] == job_id:
                        if self.has_cancellation_flag(job_id):
                            return self.build_job_response(job,"canceled (error)")
                        else:
                            return self.build_job_response(job,"error")
                else:
                    if self.has_cancellation_flag(job_id):
                        response["jobs"].append(self.build_job_response(job,"canceled (error)"))
                    else:
                        response["jobs"].append(self.build_job_response(job,"error"))
        
        if state == "in-progress" or state == "cancled" or not state:
            job = self.get_current_job()
                if job:
                    if job_id:
                        if job["jobId"] == job_id:
                            if self.has_cancellation_flag(job_id):
                                return self.build_job_response(job,"canceled (in-progress)")
                            else:
                                return self.build_job_response(job,"in-progress")
                    else:
                        if self.has_cancellation_flag(job_id):
                            response["jobs"].append(self.build_job_response(job,"canceled (in-progress)"))
                        else:
                            response["jobs"].append(self.build_job_response(job,"in-progress"))
            
    def cmd_cancel_job(self, req_payload):
        if "jobId" in req_payload:
            job_id = req_payload["jobId"]
        else:
            raise MissingArgumentException("jobId")
        
        job = None
        for job in list(self.input_queue):
            if job["jobId"] == job_id:
                self.add_cancellation_flag(job_id)
                return self.build_job_response(job,"canceled")
        job = self.get_current_job()
        if job and job["jobId"] == job_id:
            self.add_cancellation_flag(job_id)
            return self.build_job_response(job,"canceled")
        raise ApiException("The job with the ID '"+job_id+"' is unknown")
                
    
        
     
    
        
                
        
                
        
        
        
