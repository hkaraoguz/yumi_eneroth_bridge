#!/usr/bin/env python

import socket
import rospy
import sys
import time

from yumi_eneroth_bridge.msg import *
from yumi_manager.msg import SceneObjects


class EnerothYumiClient():

    def __init__(self,host='192.168.1.118',port=5000,client_type='yumi'):
        self.socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5.0)
        self.host = host #"192.168.1.118" # needs to be in quote
        self.port = port
        self.client_type=client_type
        self.pub = rospy.Publisher('yumi_eneroth_bridge/command', Command, queue_size=1)
        self.sub = rospy.Subscriber("yumi_manager/scene_objects",SceneObjects,self.process_scene_update);

    def connect(self):
        try:
           self.socket.connect((self.host, self.port))
        except Exception as ex:
           print str(ex)
           return False

        time.sleep(1)
        self.socket.send("client_type;{}".format(self.client_type).encode("utf-8"))

        return True

    def listen(self):
        buf = []
        try:
            buf = self.socket.recv(4096)
            #buf += s.recv(1)
            if len(buf) > 0:
                rospy.loginfo("Received : %s",str(buf))
            return buf
        except:
            return buf

    def close(self):
        self.send_data("close me".encode("utf-8"))
        time.sleep(1)
        self.socket.close()

    def send_data(self, data):
        try:
            self.socket.send(data)
            time.sleep(1)
        except Exception as ex:
            print str(ex)
            rospy.signal_shutdown("Socket connection failure")


    def process_scene_update(self,msg):

        #yumi is busy just send back busy msg
        if msg.yumi_status ==1:
            data="kernel;yumi_busy;"
            self.send_data(data)
            return;

        data = 'kernel;update;'
        for obj in msg.array:
            #print obj

            data +=str(obj.metricpostablecenterx)
            data +=','
            data += str(obj.metricpostablecentery)
            data +=",0.0,0.0;"

        print data

        self.send_data(data)






    def parsedata(self,data):

        data_arr = data.split(";")

        if data_arr[0] == 'home':
            command = Command()
            command.type = data_arr[0];
            self.pub.publish(command)
            return

        if len(data_arr) < 3:
            rospy.logwarn("Received data %s seems corrupt. Skipping...", data_arr);
            return
        ''''
        pos_arr = data_arr[1].split(";")

        if len(pos_arr) < 2:
            rospy.logwarn("Received pose data %s seems corrupt. Skipping...", pos_arr);
            return
        '''
        command = Command()
        command.type = data_arr[0];
        command.posx = round(float(data_arr[1]),3)
        command.posy = round(float(data_arr[2]),3)

        self.pub.publish(command)




if __name__ == '__main__':


    rospy.init_node('yumi_eneroth_bridge')

    enerothclient = EnerothYumiClient()

    if(not enerothclient.connect()):
        sys.exit(-1)

    rospy.loginfo("Yumi Eneroth bridge started...");

    while not rospy.is_shutdown():
        data = enerothclient.listen()
        if len(data) > 0 :
            enerothclient.parsedata(data)



    enerothclient.close()
