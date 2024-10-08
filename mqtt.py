from paho.mqtt import client as mqtt_client
import logging
import queue
import time
import threading

class Mqtt:
    
    AUTO_RECONNECT_DELAY = 3
    
    def __init__(self):        
        self.queue = queue.Queue(1000)
        self.subscribed_topics = []
        
        self.status_callback = []
    
    def add_status_callback(self, fct):
        self.status_callback.append(fct)

    def connect(self,broker,port,client_id,username=None,password=None):
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT broker "+broker)
                for callback in self.status_callback:
                    callback(True)
            else:
                logging.error("Could not connect to MQTT broker "+broker)
                for callback in self.status_callback:
                    callback(False)
                
        def on_disconnect(client, userdata, rc):
            logging.warning("Disconnected with result "+str(rc))
            
            while True:
                logging.info("Reconnecting to MQTT broker in "+str(Mqtt.AUTO_RECONNECT_DELAY)+" s")
                time.sleep(Mqtt.AUTO_RECONNECT_DELAY)
                try:
                    self.client.reconnect()
                    logging.info("Reconnected to MQTT broker")
                    for topic in self.subscribed_topics:
                        self.client.subscribe(topic)
                    for callback in self.status_callback:
                        callback(True)
                    return
                except Exception as err:
                    logging.error("Could not reconnect to MQTT broker")
                    for callback in self.status_callback:
                        callback(False)
                
            
        self.client = mqtt_client.Client(client_id)
        if username and password:
            self.client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        try:
            self.client.connect(broker,port)
        except Exception as e:
            return False
        return True

    def subscribe(self, topic):
        self.subscribed_topics.append(topic)
        self.client.subscribe(topic)
    
    def unsubscribe(self, topic):
        self.subscribed_topics.remove(topic)
        self.client.unsubscribe(topic)
    
    def set_on_message(self, fct):
        self.client.on_message = fct
        
    def publish(self, topic, payload, retry = False):
        result = self.client.publish(topic,payload)
        if result[0] == 0:
            logging.info("Message published to topic "+topic)
        else:
            logging.error("Could not publish message on topic "+topic)
            if retry:
                self.publish_async(topic,payload)
                    
    def publish_async(self, topic, payload):
        logging.info("Schedule message for publishing to topic "+topic)
        self.queue.put((topic,payload))
    
    def start(self,cancel_event):
        self.publisher_thread = threading.Thread(target=self.publishing_worker, args=(cancel_event,),daemon=False)
        self.publisher_thread.start()
        self.client.loop_start()
        
    def stop(self):
        self.client.loop_stop()
        self.publisher_thread.stop()
    
    def publishing_worker(self,cancel_event):
        while not cancel_event.is_set():
            if not self.queue.empty():
                msg = self.queue.get()
                self.publish(msg[0],msg[1],True)
            time.sleep(0.5)
         
                
        
