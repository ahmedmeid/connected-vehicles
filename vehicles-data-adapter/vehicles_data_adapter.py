import logging,datetime,json
import paho.mqtt.client as mqtt
import requests
from threading import Lock
from time import sleep

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('DeviceStateUpdater')
logger.setLevel(logging.INFO)


class StateServer(mqtt.Client):

    def __init__(self, settings, device_ids, keepalive=60):
        logger.info('initializing...')

        # ... set all device states to 'unknown' ...

        self._settings = settings
        self._device_ids = device_ids
        self._keepalive = keepalive

        self.id_token = ''

        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        super(StateServer, self).__init__()

    def connect(self):
        logger.info('connecting...')
        self.username_pw_set(self._settings['mqtt_broker_username'], self._settings['mqtt_broker_password'])

        super(StateServer, self).connect(self._settings['mqtt_broker_hostname'],
                                         self._settings['mqtt_broker_port'],
                                         keepalive=self._keepalive)
        self.loop_start()

        while True:

            with self._lock:
                if self._connected:
                    break

            sleep(1)

    def disconnect(self):
        logger.info('disconnecting...')
        with self._lock:
            # if already disconnected, don't do anything
            if not self._connected:
                return

        super(StateServer, self).disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, client, userdata, flags, rc):
        # successful connection
        if rc == 0:
            logger.info('successful connection')

            # ... set all device states to 'disconnected' ...

            # subscribe to all state channels
            self.subscribe('states/#', qos=2)
            self.subscribe('data/#', qos=2)
            # ping all devices to see if they are connected
            for device_id in self._device_ids:
                logger.info('pinging device: {}'.format(device_id))
                self.publish('pings/{d_id}'.format(d_id=device_id), '', qos=2)
            request = {
                            "username": self._settings['authorization_username'],
                            "password": self._settings['authorization_password'],
                            "rememberMe": True
                            }
            jout = json.dumps(request)
            headers = {'Content-type': 'application/json'}
            print("request ",jout)
            response = requests.post(self._settings['authorization_url'],headers=headers,data=jout)
            if response.status_code == 200:
                token = response.content.decode('utf-8')
                token_json = json.loads(token)
                self.id_token = token_json['id_token']
                print ("id_token ",self.id_token)

            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        logger.info('disconnected')
        with self._lock:
            self._connected = False

    def on_message(self, client, userdata, msg):
        print("received a message")
        topic_prefix, device_id = msg.topic.split('/')
        print("device id ", device_id)
        if topic_prefix == 'states':
            self.update_status(device_id,msg)
        if topic_prefix == 'data':
            self.send_data(msg)

    def update_status(self, device_id, msg):
        msg.payload = msg.payload.decode("utf-8")
        data = msg.payload
        headers = {'Content-type': 'application/json', 'Authorization' : 'Bearer '+self.id_token}
        response = requests.put(self._settings['status_service_url'], headers=headers, data=data)
        print("response ", response)

    def send_data(self, msg):
        msg.payload = msg.payload.decode("utf-8")
        data = msg.payload
        headers = {'Content-type': 'application/json', 'Authorization' : 'Bearer '+self.id_token}
        response = requests.post(self._settings['data_service_url'], headers=headers, data=data)
        print("response ", response)

if __name__ == '__main__':
    with open('config.json') as config_file:
    	settings = json.load(config_file)

    state_server = StateServer(settings, device_ids=['YS2R4X20005399401','VLUR4X20009093588',
                                                     'VLUR4X20009048066','YS2R4X20005388011',
                                                     'YS2R4X20005387949','YS2R4X20005387055'])
    state_server.connect()

    while True:

        # ... replace sleeping below with doing some useful work ...
        logger.info('sleeping for 1 sec')
        sleep(1)
