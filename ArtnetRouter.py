import json
import logging
import time
from multiprocessing import Queue
from multiprocessing import Event

from ArtnetServer import ArtnetServer
from ConfigParser import ConfigParser
from ArtnetUtils import time_in_millis


class ArtnetRouter:
    """
    Listens for data and forwards it to one or more Pixelblazes.  Designed to run in its own
    process, and communicate with the main process via Queues.
    """
    receiver = None
    pixelsPerUniverse = 170
    pixelCount = 0
    dataReady = False
    notifyTimer = 0
    FrameCount = 0
    delay = 0.033333  # default to 30 fps outgoing limit
    notify_ms = 3000  # throughput check every <notify_ms> milliseconds
    show_fps = False
    configFileName = "./config/config.conf"

    config = None
    universes = []
    deviceList = None

    pixels = []

    def __init__(self, cmdQueue: Queue, dataQueue: Queue, ui_is_active: Event, exit_flag: Event):
        logging.basicConfig(level=logging.DEBUG)

        self.cmdQueue = cmdQueue
        self.dataQueue = dataQueue
        self.ui_is_active = ui_is_active
        self.exit_flag = exit_flag

        jim = ConfigParser()
        self.config, self.deviceList, self.universes = jim.load(self.configFileName)
        print(json.dumps(self.config, indent=4))

        # print the value for each key in deviceList
        for key in self.deviceList:
            print(key + " : " + str(self.deviceList[key]))

        # print the value for each key in universes
        for key in self.universes:
            u = self.universes[key]
            # print each key and value
            for k in u:
                print(k)

        # bind multicast receiver to specific IP address
        logging.debug("Binding to %s" % self.config['listenAddress'])
        self.notifyTimer = time_in_millis()

        # loop 'till we're done, listening for packets and forwarding the pixel data
        # to Pixelblazes
        self.receiver = ArtnetServer(self.main_dispatcher)

        # send current data frame to each Pixelblaze and periodically
        # send updated status information to the UI queue, where
        # the WebUI can display it if anybody's watching.
        while True:
            try:
                if self.exit_flag.is_set():
                    break
                elapsedTime = (time_in_millis() - self.notifyTimer)
                updateUI = (elapsedTime >= self.config['statusUpdateIntervalMs'])

                for key in self.deviceList:
                    dd = self.deviceList[key]
                    dd.sendMethod()
                    if updateUI:
                        if ui_is_active.is_set():
                            self.dataQueue.put(dd.getStatusString(elapsedTime / 1000))
                        dd.resetCounters()

                if updateUI:
                    self.notifyTimer = time_in_millis()

            except KeyboardInterrupt:
                # this throws us out of the loop and into the shutdown sequence
                break

            except Exception as e:
                logging.error("ArtnetRouter: Exceptional exception" + str(e))
                logging.error("Pixelblaze probably disconnected or stalled.")
                logging.error("Sleeping it off.  Will attempt to reconnect shortly.")
                time.sleep(5)

        self.exit_flag.set()
        self.shutdown()

    def setPixelsPerUniverse(self, pix):
        self.pixelsPerUniverse = max(1, min(pix, 170))  # clamp to 1-170 pixels

    def setThroughputCheckInterval(self, ms):
        self.notify_ms = max(500, ms)  # min interval is 1/2 second, default should be about 3 sec

    def shutdown(self):
        # stop all devices in DeviceList
        for key in self.deviceList:
            logging.debug("Stopping device: " + self.deviceList[key].name)
            self.deviceList[key].stop()

        # stop listening for Artnet packets
        logging.debug("Stopping Artnet Receiver")
        del self.receiver

    def main_dispatcher(self, addr, data):
        """Test function, receives data from server callback."""
        # universe, subnet, net = decode_address_int(addr)
        # print("%d, subnet %d, net %d" % (universe, subnet, net))

        # test against the universe fragments in universes and print any matches
        for key in self.universes:
            u = self.universes[key]
            for k in u:
                if k.address_mask == addr:
                    k.device.process_pixel_data(data, k.startChannel, k.destIndex, k.pixelCount)
