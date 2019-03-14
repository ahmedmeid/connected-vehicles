import logging,time,sys,random,json,datetime
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('DeviceStateUpdater')
logger.setLevel(logging.INFO)


class DeviceStateUpdater(mqtt.Client):

    def __init__(self, settings, device_id, keepalive=60):
        logger.info('initializing...')
        self._settings = settings
        self._keepalive = keepalive
        self.device_id = device_id
        self._state_topic = 'states/{}'.format(device_id)
        self._ping_topic = 'pings/{}'.format(device_id)
        self._vehicle_data_topic = 'data/{}'.format(device_id)

        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        super(DeviceStateUpdater, self).__init__()

    def connect(self):
        logger.info('connecting...')
        self.username_pw_set(self._settings['mqtt_broker_username'], self._settings['mqtt_broker_password'])
        data = '{ "vehicleId" : "' + self.device_id + '", "status" : "DISCONNECTED", "lastUpdated" : "' + datetime.datetime.now().isoformat() + 'Z"}';
        self.will_set(self._state_topic, data, qos=2)

        super(DeviceStateUpdater, self).connect(self._settings['mqtt_broker_hostname'],
                                                self._settings['mqtt_broker_port'],
                                                keepalive=self._keepalive)
        self.loop_start()

        while True:

            with self._lock:
                if self._connected:
                    logger.info('CONNECTED')
                    break

            sleep(1)

    def disconnect(self):
        logger.info('disconnecting...')
        with self._lock:
            # if already disconnected, don't do anything
            if not self._connected:
                return

        # inform the state server that the device will disconnect
        #self.publish(self._state_topic, 'DISCONNECTED', qos=2)
        self.publishStatus('DISCONNECTED')
        # sleep for 3 secs so we receive TCP acknowledgement for the above message
        sleep(3)
        super(DeviceStateUpdater, self).disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, client, userdata, flags, rc):
        # successful connection
        if rc == 0:
            logger.info('successful connection')

            # inform the state server that the device is connected
            #self.publish(self._state_topic, 'CONNECTED', qos=2)
            self.publishStatus('CONNECTED')
            # subscribe to the ping topic so when the server pings the device can respond with a pong
            self.subscribe(self._ping_topic, qos=2)

            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        logger.info('on_disconnect')
        with self._lock:
            self._connected = False

    def on_message(self, client, userdata, msg):
        # when message is received from the ping topic respond with pong ('connected' state)
        if msg.topic == self._ping_topic:
            logger.info('received ping. responding with state')
            #self.publish(self._state_topic, 'CONNECTED', qos=2)
            self.publishStatus('CONNECTED')

    def sendData(self):
        slat = 24.734659
        slong = 46.665124
        offset = random.random()
        lat = slat + offset
        offset = random.random()
        long = slong + offset
        vehicle_data ={
            "fuelLevel": 0.60,
            "latitude": lat,
            "longitude": long,
            "speed": 60,
            "timeStamp": datetime.datetime.now().isoformat()+"Z",
            "vehicleId": self.device_id
        }
        jout=json.dumps(vehicle_data)
        print("vehicle data: ", jout)
        self.publish(self._vehicle_data_topic, jout, qos=2)

    def publishStatus(self, status):
        data = '{ "vehicleId" : "' + self.device_id + '", "status" : "' + status + '", "lastUpdated" : "' + datetime.datetime.now().isoformat() + 'Z"}';
        print("vehicle status: ", data)
        self.publish(self._state_topic, data, qos=2)


if __name__ == '__main__':
    with open('config.json') as config_file:
        settings = json.load(config_file)

    device_state_updater = DeviceStateUpdater(settings, device_id=str(sys.argv[1]))
    device_state_updater.connect()

    count = 0
    while count < int(sys.argv[2]):
        device_state_updater.sendData()
        logger.info('sleeping for 5 sec')
        sleep(5)
        count += 1
