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
    
    JOB_SCHEDULED = 0
    JOB_IN_PROGRESS = 1
    JOB_COMPLETED = 2
    JOB_MANUALLY_CANCELED = 3
    JOB_SHUTDOWN_CANCELED = 4
    JOB_ERROR = 5
    
    def __init__(self, configuration_handler):
        self.configuration = configuration_handler
        
        self.input_queue = queue.Queue(100)
        self.job_list = []
        
        #self.output_queue = queue.Queue(10000)
        #self.error_queue = queue.Queue(10000)
        #self.current_job = None
        
        self._job_list_lock = threading.Lock()
        
        self.cancellations = set()
        self._cancellation_lock = threading.Lock()
        
        self._current_job_lock = threading.Lock()
        
        self.update_callback = []
        self.status_callback = []
        
    def start(self,cancel_event):
        self.client = Minio(self.configuration.get("s3","Server"),self.configuration.get("s3","AccessKey"),self.configuration.get("s3","SecretKey"), secure=False)
        
        self.upload_worker_thread = threading.Thread(target=self.upload_worker,args=(cancel_event,),daemon=False)
        self.upload_worker_thread.start()
        
    def add_job(self, job):
        self.input_queue.put(job, block=False)
        with self._job_list_lock:
            self.job_list.append((job,self.JOB_SCHEDULED))
    
    def update_job_state(self, job_id, state):
        with self._job_list_lock:
            for i in range(len(self.job_list)):
                if self.job_list[i][0]["jobId"] == job_id:
                    self.job_list[i] = (self.job_list[i][0],state)
    
    def get_job(self, job_id):
        with self._job_list_lock:
            for i in range(len(self.job_list)):
                if self.job_list[i][0]["jobId"] == job_id:
                    return self.job_list[i]
        return None
    
    
    
    #def add_cancellation_flag(self, jobId):   
        #with self._cancellation_lock:
        #    if not jobId in self.cancellations:
        #        self.cancellations.add(jobId)
    
    #def remove_cancellation_flag(self, jobId):
    #    with self._cancellation_lock:
    #        self.cancellations.discard(jobId)
    
    def has_cancellation_flag(self, job_id):
        #with self._cancellation_lock:
        #    return jobId in self.cancellations
        with self._job_list_lock:
            for i in range(len(self.job_list)):
                if self.job_list[i][0]["jobId"] == job_id:
                    if self.job_list[i][1] == self.JOB_MANUALLY_CANCELED:
                        return True
                    else:
                        return False
        return False

    #def set_current_job(self, job):
    #    with self._current_job_lock:
    #        self.current_job = job
    
    #def get_current_job(self):
    #    with self._current_job_lock:
    #        return self.current_job
    
    #def remove_current_job(self):
    #    with self._current_job_lock:
    #        self.current_job = None
        
    def add_update_callback(self, fct):
        self.update_callback.append(fct)
        
    def add_status_callback(self, fct):
        self.status_callback.append(fct)
        
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
                # TODO: check what happens if directory contains sub folders
                if not cancel_event.is_set():
                    if not self.has_cancellation_flag(jobId):
                        logging.info("Upload "+os.path.join(path,file)+" to bucket "+bucket)
                        self.client.fput_object(bucket,file,os.path.join(path,file))
                        for callback in self.update_callback:
                            callback(jobId,len(dir),i+1,path)
                        
                    else:
                        logging.info("Job '"+str(jobId)+"' manually canceled.")
                        for callback in self.status_callback:
                            callback(jobId,self.JOB_MANUALLY_CANCELED)
                        
                        #self.remove_current_job()
                        #self.output_queue.put(job)
                        return 
                else:
                    logging.info("Job '"+str(jobId)+"' canceled due to shutdown.")
                    for callback in self.status_callback:
                        callback(jobId,self.JOB_SHUTDOWN_CANCELED)
                    self.update_job_state(jobId, self.JOB_SHUTDOWN_CANCELED)
                    #self.remove_current_job()
                    #self.error_queue.put(job)
                    return 
            for callback in self.status_callback:
                callback(jobId,self.JOB_COMPLETED)
            self.update_job_state(jobId, self.JOB_COMPLETED)
            #self.remove_current_job()
            #self.output_queue.put(job)
        except Exception as exc:
            logging.error("Job '"+str(jobId)+"' ended with exception '"+str(type(exc))+"'") 
            logging.exception(exc)
            for callback in self.status_callback:
                callback(jobId,self.JOB_ERROR)
            self.update_job_state(jobId, self.JOB_ERROR)
            #self.remove_current_job()
            #self.error_queue.put(job)
            
    def upload_worker(self, cancel_event):
        while not cancel_event.is_set():
            if not self.input_queue.empty():
                job = self.input_queue.get()
                if not self.has_cancellation_flag(job["jobId"]):
                    self.update_job_state(job["jobId"], self.JOB_IN_PROGRESS)
                    logging.info("Job '"+str(job["jobId"])+"' loaded") 
                    self.upload(job,cancel_event)
            time.sleep(0.5)
            
    def request(self, req_payload):
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
        if state == self.JOB_SCHEDULED:
            state = "scheduled"
        elif state == self.JOB_IN_PROGRESS:
            state = "in-progress"
        elif state == self.JOB_COMPLETED:
            state = "completed"
        elif state == self.JOB_MANUALLY_CANCELED:
            state = "canceled"
        elif state == self.JOB_SHUTDOWN_CANCELED:
            state = "canceled-shutdown"
        elif state == self.JOB_ERROR:
            state = "error"
        else:
            state = "unknown"
        
        response = {
            "jobId": job["jobId"],
            "bucket": job["bucket"],
            "path": job["path"],
            "state": state
            #"requestTopic": self.configuration.get("api","RequestJobsTopic"),
            #"requestTopic": self.configuration.get("api","ResponseJobsTopic")+"/"+job["jobId"].replace(" ","-").replace("#","-").replace("*","-")
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
            bucket = self.configuration.get("device","DeviceId")+datetime.now().strftime("%m%d%Y%H%M%S")
            
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
            
        response = {
            "jobs": []
        }
        
        if state == "scheduled":
            state = self.JOB_SCHEDULED
        elif state == "in-progress":
            state = self.JOB_IN_PROGRESS
        elif state == "completed":
            state = self.JOB_COMPLETED
        elif state == "canceled":
            state = self.JOB_MANUALLY_CANCELED
        elif state == "canceled-shutdown":
            state = self.JOB_SHUTDOWN_CANCELED
        elif state == "error":
            state = self.JOB_ERROR
        else:
            state = None
            
        with self._job_list_lock:
            for job in self.job_list:
                if not job_id or (job_id == job["jobId"]):
                    if not state or (state == job[1]):
                        response["jobs"].append(self.build_job_response(job[0],job[1]))
        
        return response
    
    def state_response(self,job_id,state):
        if state == self.JOB_SCHEDULED:
            state = "scheduled"
        elif state == self.JOB_IN_PROGRESS:
            state = "in-progress"
        elif state == self.JOB_COMPLETED:
            state = "completed"
        elif state == self.JOB_MANUALLY_CANCELED:
            state = "canceled"
        elif state == self.JOB_SHUTDOWN_CANCELED:
            state = "canceled-shutdown"
        elif state == self.JOB_ERROR:
            state = "error"
        else:
            state = "unknown"
            
        payload = {
            "jobId": job_id,
            "state": state
        }
        return payload
    
    def update_response(self,job_id,total,completed,path):
        payload = {
            "jobId": job_id,
            "total": total,
            "completed": completed,
            "lastUploadedItem": path
        }
        return payload
            
    def cmd_cancel_job(self, req_payload):
        if "jobId" in req_payload:
            job_id = req_payload["jobId"]
        else:
            raise MissingArgumentException("jobId")
        
        self.update_job_state(job_id,self.JOB_MANUALLY_CANCELED)
        job = self.get_job(job_id)
        if job:
            return self.build_job_response(job[0],job[1])
        else:
           raise ApiException("The job with the ID '"+job_id+"' is unknown") 

        
                
    
        
     
    
        
                
        
                
        
        
        
