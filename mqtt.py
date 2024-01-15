from paho.mqtt import client as mqtt_client
import logging
import queue
import time
import threading

class Mqtt:
    
    AUTO_RECONNECT_DELAY = 3
    
    def __init__(self):        
        self.queue = queue.Queue(1000)

    def connect(self,broker,port,client_id,username=None,password=None):
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Connected to MQTT broker "+broker)
            else:
                logging.error("Could not connect to MQTT broker "+broker)
                
        def on_disconnect(client, userdata, rc):
            logging.warning("Disconnected with result "+str(rc))
            
            while True:
                logging.info("Reconnecting to MQTT broker in "+str(AUTO_RECONNECT_DELAY)+" s")
                time.sleep(self.AUTO_RECONNECT_DELAY)
                try:
                    self.client.reconnect()
                    logging.info("Reconnected to MQTT broker")
                    return
                except Exception as err:
                    logging.error("Could not reconnect to MQTT broker")
                
            
        self.client = mqtt_client.Client(client_id)
        if username and password:
            self.client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.connect(broker,port)
        self.on_disconnect = on_disconnect
    
    def subscribe(self, topic):
        self.client.subscribe(topic)
    
    def unsubscribe(self, topic):
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
        self.client.loop_forever()
        
    def stop(self):
        self.client.loop_stop()
        self.publisher_thread.stop()
    
    def publishing_worker(self,cancel_event):
        while not cancel_event.is_set():
            if not self.queue.empty():
                msg = self.queue.get()
                self.publish(msg[0],msg[1],True)
            time.sleep(0.5)
         
                
        