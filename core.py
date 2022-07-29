import time

import jwt
import numpy as np

from paho.mqtt import client as mqtt_client
import csv
from datetime import datetime, timedelta
import ssl
from random import randrange
from pymongo import MongoClient

CA_CERTS = "ca.pem"
CERT_FILE = "client.pem"
KEY_FILE = "client.key"


class Credentials:
    CA_CERTS = "ca.pem"
    CERT_FILE = "client.pem"
    KEY_FILE = "client.key"
    HEADER = {"alg": "ES256", "typ": "JWT"}

def get_er():
    er = randrange(100000, 1000000000)
    return er


def is_speed_max(speed):
    return speed == "max"


class Gateway:
    def __init__(self, gateway_id, speed, number_of_devices, payload_size):
        self.id = gateway_id
        self.gateway_topic = "/stratosfy/" + self.id + "/"

        # self.sensor_topic = self.generate_sensor_topics(number_of_devices)
        self.number_of_devices = number_of_devices
        self.client = mqtt_client.Client(self.id)
        self.received_messages = dict()
        self.sent_messages = dict()
        self.sent_messages_time = dict()
        self.received_messages_time = dict()
        self.speed = speed
        self.payload_size = payload_size
        self.sent_messages_number = 0

    def get_sent_message_dict_key(self, msg):
        return msg.split('\n"er": ', 1)[1][:-1]

    def message_to_save_on_received_messages(self, msg):
        return datetime.now()

    def message_to_save_on_sent_messages(self, msg):
        return datetime.now()

    def get_sending_to_cloud_devices_data(self):
        data = []
        #data.append(self.generate_data_to_cloud_device(get_er()))
        for i in range(self.number_of_devices + 1):
            data.append(self.generate_data_to_cloud_device(get_er()))
        return data

    def get_send_to_cloud_topic(self):
        return self.gateway_topic + "telemetry"

    def generate_data_to_cloud_device(self, i):
        import time
        message_to_send = dict()
        gt = time.time()

        gd = "5C78FEBF" + str(self.sent_messages_number)
        er = int(i)
        tt = time.time()
        message_to_send["gt"] = (int)(gt)
        message_to_send["tt"] = (int)(tt)
        message_to_send["gd"] = gd
        message_to_send["er"] = er
        return str(message_to_send)

    def publish(self, start_time, period):
        # Preparing messages
        msg_list = self.get_sending_to_cloud_devices_data()
        for msg_idx, msg in enumerate(msg_list):

            msg = str(msg)
            msg = msg.replace('\'', '"')
            msg = msg.replace(', ', ',\n')
            print("topic payload", self.get_send_to_cloud_topic(), self.filler(str(msg)))
            # print("msg_idx, msg: ", msg_idx, msg)

            #if msg_idx == 0:
            result = self.client.publish(topic=self.get_send_to_cloud_topic(), payload=self.filler(str(msg)))
            self.sent_messages_number += 1
            self.sent_messages[self.get_sent_message_dict_key(msg)] = self.message_to_save_on_sent_messages(msg)
            self.sent_messages_time[msg] = datetime.now()
            if not is_speed_max(self.speed):
                time.sleep(period.total_seconds() / self.speed)
            status = result[0]
            if status == 0:
                pass
            else:
                print(f"Failed to send message")

    def filler(self, message):
        result = message
        if len(message) < self.payload_size:
            result += (self.payload_size - len(message)) * "."
        return result


def get_password(username, private_key):
    payload = dict(aud="snowm-bridge-gw", cid=username, iat=datetime.now().timestamp(),
                   exp=(datetime.now() + timedelta(minutes=10)).timestamp())
    HEADER = {"alg": "ES256", "typ": "JWT"}
    encoded_jwt = jwt.encode(headers=HEADER, payload={"payload": payload}, key=private_key,
                             algorithm="ES256")
    return encoded_jwt


def generate_device_id(i):
    # print(i, (Credentials.USERNAMES))
    return Credentials.USERNAMES[i]


def authenticate_client(gateway, username, private_key):
    # gateway.get_client().username_pw_set(username, password)
    gateway.client.tls_set(ca_certs=Credentials.CA_CERTS, certfile=Credentials.CERT_FILE,
                           keyfile=Credentials.KEY_FILE,
                           cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
    gateway.client.tls_insecure_set(True)
    gateway.client.username_pw_set(username, get_password(username, private_key))
    return gateway


def set_connection(gateway):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            connected_to_mqtt_broker = "Connected to MQTT Broker!"
            print(connected_to_mqtt_broker)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(client, userdata, message):
        msg = str(message.payload.decode("utf-8"))
        print("on_message: ", msg)
        print("topic: ", message.topic)
        gateway.received_messages[msg] = gateway.message_to_save_on_received_messages(msg)

        received_time = datetime.now()
        gateway.received_messages_time[msg] = received_time
        # print("topic: ", message.topic)
        # print("msg: ", msg)

    def on_publish(client, userdata, result):  # create function for callback
        # broker_received_messages.
        data_published = "data_published"
        # print("on_publish", result, userdata)

    gateway.client.on_connect = on_connect

    gateway.client.on_message = on_message
    gateway.client.on_publish = on_publish

    gateway.client.connect(Core.broker, Core.port)
    return gateway


class Core:
    broker = 'mqtt.staging.genius.stratosfy.io'
    port = 8883
    period = timedelta(seconds=10)
    duration = timedelta(seconds=40)
    mean = (period / 4).total_seconds()
    std = (period / 10).total_seconds()

    number_of_devices_per_gateway = 1
    payload_size = 0

    def __init__(self, number_of_gateways, gateway_speed):
        self.number_of_gateways = number_of_gateways
        self.gateway_speed = gateway_speed
        # Creating gateways
        self.gateways = self.generate_gateways(gateway_speed)

    def read_file(self):
        with open('credentials.txt') as f:
            contents = f.read()
            # print(contents.split("\n")[:10])
            contents = contents.split("\n")
        usernames = []
        inside_private_key = False
        private_key = ""
        private_keys = []
        for c in contents:

            if c == "-----END EC PRIVATE KEY-----":
                inside_private_key = False
                private_key += "\n" + c
                private_keys.append(private_key)
                private_key = ""

            if inside_private_key:
                private_key += c

            if c == "-----BEGIN EC PRIVATE KEY-----":
                inside_private_key = True
                private_key += c + "\n"

            if c.startswith("STSFY-"):
                usernames.append(c)

        return usernames, private_keys

    def generate_gateways(self, speed):
        gateway_list = []
        Credentials.USERNAMES, Credentials.PRIVATE_KEYS = self.read_file()
        for i in range(self.number_of_gateways):
            # Initializing gateway
            result_gateway = Gateway(generate_device_id(i), speed,
                                     number_of_devices=Core.number_of_devices_per_gateway,
                                     payload_size=Core.payload_size)
            result_gateway = authenticate_client(result_gateway, Credentials.USERNAMES[i],
                                                 Credentials.PRIVATE_KEYS[i])
            result_gateway = set_connection(result_gateway)
            # Saving the gateway
            gateway_list.append(result_gateway)
        result_gateways = gateway_list
        return result_gateways

    def send_process(self, gateway):
        from datetime import datetime
        start_time = datetime.now()
        for i in range(int(self.duration.total_seconds() / self.period.total_seconds())):
            # TODO check if the gateway period has been reached
            gateway.publish(start_time, self.period)
            current_time = datetime.now()
            if (current_time - start_time).total_seconds() < self.period.total_seconds() * (i + 1):
                nothing = 0

            else:
                print("no time sleep: ", (current_time - start_time).total_seconds(),
                      self.period.total_seconds() * (i + 1),
                      (self.period * (i + 1) - (current_time - start_time)).total_seconds())
        # gateway.client.disconnect()

    def run(self):
        import threading
        thread_list = []
        for gateway in self.gateways:
            try:
                th = threading.Thread(target=self.send_process, args=(gateway,))
                thread_list.append(th)
            except:
                print("Cannot start thread")

        sleep_time_to_start = np.random.normal(self.mean, self.std, len(self.gateways))
        sleep_time_to_start = sorted(sleep_time_to_start)
        print(sleep_time_to_start)
        tmp = []
        previous = 0
        for i in sleep_time_to_start:
            tmp.append(max(0, i - previous))
            previous = i
        sleep_time_to_start = tmp
        print("sleep_time_to_start: ", sleep_time_to_start)
        for i, th in enumerate(thread_list):
            th.start()
            time.sleep(sleep_time_to_start[i])

        for th in thread_list:
            th.join()

        for gateway in self.gateways:
            gateway.client.disconnect()

        # return gateways


class DatabaseRetrieval:

    def __init__(self, device_id, start_time, end_time):

        # Convert time to datetime
        start_time_edited = datetime.strptime(start_time, "%Y%m%d%H%M")
        end_time_edited = datetime.strptime(end_time, "%Y%m%d%H%M")

        # Connecting to db
        new_staging = "mongodb://staging_mongo_user:M2li6JSLvVfe1uOj@stratosfy-genius-stagin-shard-00-00.6gn88" \
                      ".mongodb.net:27017,stratosfy-genius-stagin-shard-00-01.6gn88.mongodb.net:27017," \
                      "stratosfy-genius-stagin-shard-00-02.6gn88.mongodb.net:27017/myFirstDatabase?ssl=true" \
                      "&replicaSet=atlas-12o1ux-shard-0&authSource=admin&retryWrites=true&w=majority "
        new_connection = MongoClient(new_staging, ssl_cert_reqs=ssl.CERT_NONE)
        new_db = new_connection["devices_dynamic"]

        docs = new_db[device_id].find({
            "messageStoredTime": {"$lt": end_time_edited,
                                  "$gte": start_time_edited}})  # , {"messageStoredTime": 1, "data.rawPkt": 1 ,"_id": 0})

        # for doc in docs:
        #    print("this is doc: ", doc)
        message_received_time = []
        self.message_stored_time_dict = dict()
        self.message_received_time_dict = dict()
        battery = []
        surface_temp = []
        air_temp = []
        message_count = []
        # print("start ----")
        for doc in docs:
            # print("----")
            # print(doc["messageStoredTime"])
            # print(doc["data"]["messageCount"])
            # self.message_stored_time_dict[(str)(doc["data"]["messageCount"])] = doc["messageStoredTime"]
            # try:
            self.message_stored_time_dict[(str)(doc["data"]["messageCount"])] = doc["messageStoredTime"]
            self.message_received_time_dict[(str)(doc["data"]["messageCount"])] = doc["messageReceivedTime"]

            try:
                message_count.append(float(doc["data"]["messageCount"]))
            except:
                message_count.append(-1)
            try:
                battery.append(float(doc["data"]["batteryPer"]))
            except:
                battery.append(-1)
            try:
                surface_temp.append(float(doc["data"]["surfaceTemperature"]))
            except:
                surface_temp.append(-1)
            try:
                air_temp.append(float(doc["data"]["airTemperature"]))
            except:
                air_temp.append(-1)

        # return message_count
        # print(self.message_stored_time_dict)


def get_average(l):
    try:
        return sum(l) / len(l)
    except:
        return -1


class Save:

    def __init__(self, core, gateways):
        self.gateways = gateways
        outfile = open(
            'total number of messages number of gateways = ' + str(len(self.gateways)) + ' gateway speed = ' + str(
                self.gateways[0].speed) + " - without offset.csv", 'w')
        out = csv.writer(outfile)

        rows = []
        title_row = ["Gateway ID", "Total number of messages gateway sent to the broker", "sum of stored time list",
                     "len of stored time list", "dropped message count"]
        rows.append(title_row)
        # for device_id in Credentials.USERNAMES:
        #    start_time = "202205250000"
        #    end_time = "202404182100"
        #    dbr = DatabaseRetrieval(device_id, start_time, end_time)
        #    dropped_message_num_dict = dict()
        #    stored_time_list_dict = dict()
        start_time = "202207120000"
        end_time = "202404182100"
        dropped_message_num_dict = dict()
        received_time_list_dict = dict()
        stored_time_list_dict = dict()
        sent_message_time_list = []
        received_message_time_list = []
        stored_message_time_list = []
        for gateway in self.gateways:
            print("gateway.id: ", gateway.id)
            dbr = DatabaseRetrieval(gateway.id, start_time, end_time)
            received_time_list_g = []
            stored_time_list_g = []
            dropped_message_list_g = []
            print("gateway.sent_messages.keys():", gateway.sent_messages.keys())
            print("dbr.message_stored_time_dict.keys():", dbr.message_stored_time_dict.keys())
            for sent_message_key in gateway.sent_messages.keys():
                if sent_message_key in dbr.message_stored_time_dict.keys():
                    print("I am here")
                    sent_message_time_list.append(gateway.sent_messages[sent_message_key].timestamp())
                    received_message_time_list.append(dbr.message_received_time_dict[sent_message_key].timestamp())
                    stored_message_time_list.append(dbr.message_stored_time_dict[sent_message_key].timestamp())

                    received_delay = (dbr.message_received_time_dict[sent_message_key] - gateway.sent_messages[
                        sent_message_key]).total_seconds() - 14400
                    # print("received delay: ", dbr.message_received_time_dict[sent_message_key], gateway.sent_messages[
                    #    sent_message_key], (dbr.message_received_time_dict[sent_message_key] - gateway.sent_messages[
                    #    sent_message_key]).total_seconds() - 14400)
                    received_time_list_g.append(received_delay)
                    stored_delay = (dbr.message_stored_time_dict[sent_message_key] - gateway.sent_messages[
                        sent_message_key]).total_seconds() - 14400
                    stored_time_list_g.append(stored_delay)
                else:
                    dropped_message_list_g.append(gateway.sent_messages[sent_message_key])
            dropped_message_num_dict[gateway.id] = len(dropped_message_list_g)
            # print("stored_time_list_g", len(stored_time_list_g))
            #print("received_time_list_g: ", received_time_list_g)
            received_time_list_dict[gateway.id] = received_time_list_g
            stored_time_list_dict[gateway.id] = stored_time_list_g
            # print("g.id p", [g for g in stored_time_list_dict.keys()])
        # print("g.id", [g for g in stored_time_list_dict.keys()])

        for gateway in self.gateways:
            # print("gateway.id: ", gateway.id)
            # print("stored_time_list_dict", stored_time_list_dict[gateway.id])
            if get_average(stored_time_list_dict[gateway.id]) > 0:

                gateway_row = [gateway.id,
                               len(gateway.sent_messages.keys()),
                               get_average(stored_time_list_dict[gateway.id]),
                               dropped_message_num_dict[gateway.id],
                               len(stored_time_list_dict[gateway.id])]
                rows.append(gateway_row)
            # else:
            #    gateway_row = [gateway.id, len(gateway.sent_messages.keys()), 0, dropped_message_num_dict[gateway]]

        total_row = []
        dropped_message_num_sum = 0
        stored_delay_message_avg = 0
        message_num = 0
        for gateway in stored_time_list_dict.keys():
            stored_delay_message_avg += sum(stored_time_list_dict[gateway])
            message_num += len(stored_time_list_dict[gateway])
        print("message_num", message_num)
        if message_num > 0:
            stored_delay_message_avg = stored_delay_message_avg / message_num

        received_delay_message_avg = 0
        message_num = 0
        for gateway in received_time_list_dict.keys():
            received_delay_message_avg += sum(received_time_list_dict[gateway])
            message_num += len(received_time_list_dict[gateway])
        if message_num > 0:
            received_delay_message_avg = received_delay_message_avg / message_num

        sum_of_sent_messages = 0
        sum_of_stored_messages = 0
        for row in rows[1:]:
            sum_of_sent_messages += row[1]
            sum_of_stored_messages += row[4]
            dropped_message_num_sum += row[3]
        rows.append(["Total", sum_of_sent_messages, stored_delay_message_avg, dropped_message_num_sum, sum_of_stored_messages])
        out.writerows(rows)
        outfile.close()

        print("sent_message_time_list: ", sent_message_time_list)
        print("received_message_time_list: ", received_message_time_list)
        print("stored_message_time_list: ", stored_message_time_list)

        time_now = str(datetime.now())
        outfile2 = open(
            time_now + 'sent_message_time_list number of gateways = ' + str(len(self.gateways)) + ' gateway speed = ' + str(
                self.gateways[0].speed) + " - with offset.csv", 'w')
        out2 = csv.writer(outfile2)
        out2.writerows(sent_message_time_list)
        outfile2.close()
        outfile3 = open(
            time_now + 'sent_message_time_list number of gateways = ' + str(
                len(self.gateways)) + ' gateway speed = ' + str(
                self.gateways[0].speed) + " - with offset.csv", 'w')
        out3 = csv.writer(outfile3)
        out3.writerows(stored_message_time_list)
        outfile3.close()

        sent_message_time_list = sorted(sent_message_time_list)
        received_message_time_list = sorted(received_message_time_list)
        stored_message_time_list = sorted(stored_message_time_list)

        print("After sort:")
        print(sent_message_time_list)
        print(received_message_time_list)
        print(stored_message_time_list)


        accuracy = 1

        start = sent_message_time_list[0]
        sent_message_time_list = [round((i - start) * 10 ** accuracy) / 10 ** accuracy for i in sent_message_time_list]
        received_message_time_list = [round((i - start - 14400) * 10 ** accuracy) / 10 ** accuracy for i in received_message_time_list]
        stored_message_time_list = [round((i - start - 14400) * 10 ** accuracy) / 10 ** accuracy for i in
                                    stored_message_time_list]

        print("After round:")
        print(sent_message_time_list)
        print(received_message_time_list)
        print(stored_message_time_list)

        from collections import Counter

        cntr_sent = Counter(sent_message_time_list)
        cntr_received = Counter(received_message_time_list)
        cntr_stored = Counter(stored_message_time_list)
        print(cntr_sent)
        print(cntr_received)
        print(cntr_stored)

        from matplotlib import pyplot as plt

        names_sent = list(cntr_sent.keys())
        values_sent = list(cntr_sent.values())

        names_stored = list(cntr_stored.keys())
        values_stored = list(cntr_stored.values())

        names_received = list(received_message_time_list)
        values_received = list(received_message_time_list)

        # creating the bar plot
        from matplotlib import pyplot as plt

        fig = plt.figure(figsize=(10, 5))
        plt.scatter(names_stored, values_stored, label='Stored messages')
        # plt.scatter(names_received, values_received, label='Received messages')
        plt.scatter(names_sent, values_sent, label='Sent messages')
        plt.xlabel("Time(sec)")
        plt.ylabel("Number of payloads")
        plt.xticks(np.arange(max(min(names_sent+names_received+names_stored),0), max(names_sent+names_received+names_stored) + 1, np.round((max(names_sent+names_received+names_stored) - max(min(names_sent+names_received+names_stored),0))/10)))
        plt.yticks(np.arange(0, max(values_sent + values_stored + values_received) + 1, np.round(max(values_sent + values_stored + values_received)/15)))

        plt.legend()
        plt.savefig(
            'figure1 - ' + str(len(gateways)) + " - " + str(core.gateway_speed) + ' - without normal offsets.png')


def run():
    import os
    import glob

    files = glob.glob('*.csv', recursive=True)

    credentials = dict()

    number_of_gateways = [1]
    # number_of_gateways = [1]
    # gateway_speed = [25, 50, 100, 200, 400, "max"]
    gateway_speed = [50]
    # gateway_speed = [20]
    cores = []
    for i in number_of_gateways:
        for j in gateway_speed:
            c = Core(i, j)
            c.run()
            cores.append(c)
    time.sleep(10)
    for c in cores:
        Save(core=c, gateways=c.gateways)


if __name__ == '__main__':
    run()
