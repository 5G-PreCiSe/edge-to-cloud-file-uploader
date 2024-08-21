import json
import threading
import time
import logging
import sh


class Api:
    
    STAT_INTERVALL = 2
    
    def __init__(self, configuration_handler, mqtt_client):
        self.configuration = configuration_handler
        self.mqtt = mqtt_client
        self.registered = False
        
        self.registered_callback = None
        
    def set_filesystem(self, fs):
        self.file_system = fs
        
    def set_uploader(self, s3):
        self.uploader = s3
        self.uploader.add_status_callback(self.s3_status_callback)
        self.uploader.add_update_callback(self.s3_update_callback)
        
    def start(self,cancel_event):
        self.cancel_event = cancel_event
        self.mqtt.set_on_message(self.on_receive)
        self.mqtt.subscribe(self.configuration.get("api","RequestTopicsTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestRegisterTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestSystemTopic"))
        self.mqtt.subscribe(self.configuration.get("api","ResponseSystemTopic"))
        
        self.publisher_state_thread = threading.Thread(target=self.publish_state, args=(cancel_event,),daemon=False)
        self.publisher_state_thread.start()
        
    def publish_state(self,cancel_event):
        while not cancel_event.is_set():
            res_payload = {
                "isRegistered": self.is_registered()
            }
            self.mqtt.publish_async(self.configuration.get("api","ResponseStateTopic"),json.dumps(res_payload))
            time.sleep(self.STAT_INTERVALL)
    
    def s3_status_callback(self,job_id, state):
        payload = self.uploader.state_response(job_id,state)
        self.mqtt.publish_async(self.configuration.get("api","ResponseJobsTopic"),json.dumps(payload))
        
    def s3_update_callback(self,job_id,total,completed,path):
        payload = self.uploader.update_response(job_id,total,completed,path)
        self.mqtt.publish_async(self.configuration.get("api","ResponseJobsTopic"),json.dumps(payload))
            
    def set_registered_callback(self, fct):
        self.registered_callback = fct

        
    def is_registered(self):
        return self.registered
    
    def register(self):
        self.mqtt.unsubscribe(self.configuration.get("api","RequestRegisterTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestFileSystemTopic"))
        
        self.uploader.start(self.cancel_event)
        
        self.mqtt.subscribe(self.configuration.get("api","RequestJobsTopic"))
        
        self.registered = True
        if self.registered_callback:
            self.registered_callback()
            
        return {
            "isRegistered": self.is_registered()
        }
        
    def publish_topics(self):
        response = dict()
        response["topics"] = []
        
        response["topics"].append({
            "topic": self.configuration.get("api","ResponseStateTopic"),
            "relation": "responseStateTopic"
        })
        response["topics"].append({
            "topic": self.configuration.get("api","ResponseTopicsTopic"),
            "relation": "responseTopicsTopic"
        })
        response["topics"].append({
            "topic": self.configuration.get("api","RequestTopicsTopic"),
            "relation": "requestTopicsTopic"
        })
        response["topics"].append({
            "topic": self.configuration.get("api","RequestSystemTopic"),
            "relation": "requestSystemTopic"
        })
        response["topics"].append({
            "topic": self.configuration.get("api","ResponseSystemTopic"),
            "relation": "responseSystemTopic"
        })
        
        if self.is_registered():
            response["topics"].append({
                "topic": self.configuration.get("api","ResponseFileSystemTopic"),
                "relation": "responseFileSystemTopic"
            })
            response["topics"].append({
                "topic": self.configuration.get("api","RequestFileSystemTopic"),
                "relation": "requestFileSystemTopic"
            })
            response["topics"].append({
                "topic": self.configuration.get("api","ResponseJobsTopic"),
                "relation": "reponseJobsTopic"
            })
            response["topics"].append({
                "topic": self.configuration.get("api","RequestJobsTopic"),
                "relation": "requestJobsTopic"
            })
        else:
            response["topics"].append({
                "topic": self.configuration.get("api","ResponseRegisterTopic"),
                "relation": "responseRegisterTopic"
            })
            response["topics"].append({
                "topic": self.configuration.get("api","RequestRegisterTopic"),
                "relation": "requestRegisterTopic"
            })
        return response
    
    def serve_system_request(self, req_payload):
        response = dict()
        if "command" in req_payload:
            if req_payload["command"] == "shutdown":
                self.shutdown()
            elif req_payload["command"] == "reboot":
                self.reboot()
            else:
                raise UnknownCommandException(command=req_payload["command"])
        else:
            raise MissingArgumentException(argument="command")
        response["command"] = req_payload["command"]
        return response

    def shutdown(self):
        self.cancel_event.set()
        time.sleep(3)
        sh.sudo.shutdown()
    
    def reboot(self):
        self.cancel_event.set()
        time.sleep(3)
        sh.sudo.reboot()
             
    def decode_payload(self, msg):
        if msg.payload:
            payload = msg.payload.decode()
            if payload:
                return json.loads(payload)
            else:
                return dict()
        else:
            return dict()
        
    def on_receive(self,client, userdata, msg):
        try:
            res_payload = dict()
            req_payload = dict()
            res_topic = self.configuration.get("api","ResponseErrorTopic")
            
            logging.info("Message received on "+msg.topic)
            
            if msg.topic == self.configuration.get("api","RequestTopicsTopic"):
                res_topic = self.configuration.get("api","ResponseTopicsTopic")
                req_payload = self.decode_payload(msg)
                res_payload = self.publish_topics()
            elif msg.topic == self.configuration.get("api","RequestSystemTopic"):
                res_topic = self.configuration.get("api","ResponseSystemTopic")
                req_payload = self.decode_payload(msg)
                res_payload = self.serve_system_request(req_payload)
            else:
                if not self.is_registered():
                    if msg.topic == self.configuration.get("api","RequestRegisterTopic"):
                        res_topic = self.configuration.get("api","ResponseRegisterTopic")
                        req_payload = self.decode_payload(msg)
                        self.configuration.request(req_payload)
                        res_payload = self.register()
                else:
                    if msg.topic == self.configuration.get("api","RequestFileSystemTopic"): 
                        res_topic = self.configuration.get("api","ResponseFileSystemTopic")
                        req_payload = self.decode_payload(msg)
                        res_payload = self.file_system.request(req_payload)
                    
                    elif msg.topic == self.configuration.get("api","RequestJobsTopic"):
                        res_topic = self.configuration.get("api","ResponseJobsTopic")
                        req_payload = self.decode_payload(msg)
                        res_payload = self.uploader.request(req_payload)
            
        except ApiException as ae:
            res_payload = ae.get_error_response()    
        
        except Exception as e:
            res_payload = {
                "error": str(e)
            }
        
        if "correlationId" in req_payload:
            res_payload["correlationId"] = req_payload["correlationId"]
        else:
            res_payload["correlationId"] = None   
            
        self.mqtt.publish_async(res_topic,json.dumps(res_payload))


class ApiException(Exception):
    def __init__(self, message = "API exception raised"):
        self.message = message
        super().__init__(self.message)
    
    def get_error_response(self):
        return {
            "error": self.message,
        }
        
class MissingArgumentException(ApiException):
    def __init__(self, argument, message = "Missing argument"):
        self.argument = argument
        self.message = message
        super().__init__(self.message)
    
    def get_error_response(self):
        return {
            "error": self.message,
            "argument": self.argument
        }

class UnknownCommandException(ApiException):
    def __init__(self,command,message = "Unknown command"):
        self.command = command
        self.message = message
        super().__init__(self.message)
    
    def get_error_response(self):
        return {
            "error": self.message,
            "command": self.command
        }
