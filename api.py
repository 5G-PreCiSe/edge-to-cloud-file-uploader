import json
import threading
import time

class Api:
    
    STAT_INTERVALL = 2
    
    def __init__(self, configuration_handler, mqtt_client):
        self.configuration = configuration_handler
        self.mqtt = mqtt_client
        self.registered = False
        
    def set_filesystem(self, fs):
        self.file_system = fs
        
    def set_uploader(self, s3):
        self.uploader = s3
        
    def start(self,cancel_event):
        self.cancel_event = cancel_event
        self.mqtt.set_on_message(self.on_receive)
        self.mqtt.subscribe(self.configuration.get("api","RequestTopicsTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestRegisterTopic"))
        
        self.publisher_state_thread = threading.Thread(target=self.publish_state, args=(cancel_event,),daemon=False)
        self.publisher_state_thread.start()
        
    def publish_state(self,cancel_event):
        while not cancel_event.is_set():
            res_payload = {
                "isRegistered": self.is_registered()
            }
            self.mqtt.publish_async(self.configuration.get("api","ResponseStateTopic"),json.dumps(res_payload))
            time.sleep(self.STAT_INTERVALL)

        
    def is_registered(self):
        return self.registered
    
    def register(self):
        self.mqtt.unsubscribe(self.configuration.get("api","RequestRegisterTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestFileSystemTopic"))
        
        self.uploader.start(self.cancel_event)
        
        self.mqtt.subscribe(self.configuration.get("api","RequestJobsTopic"))
        self.mqtt.subscribe(self.configuration.get("api","RequestJobsTopic")+"/#")
        
        
        self.registered = True
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
            "topic": self.configuration.get("api","RequestTopicsTopic"),
            "relation": "requestTopicsTopic"
        })
        response["topics"].append({
            "topic": self.configuration.get("api","RequestTopicsTopic"),
            "relation": "requestTopicsTopic"
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
                "topic": self.configuration.get("api","ReponseJobsTopic"),
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

            if msg.topic == self.configuration.get("api","RequestTopicsTopic"):
                res_topic = self.configuration.get("api","ResponseTopicsTopic")
                req_payload = self.decode_payload(msg)
                res_payload = self.publish_topics()
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
