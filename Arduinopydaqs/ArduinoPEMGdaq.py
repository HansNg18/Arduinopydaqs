# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 19:26:38 2020

@author: simon
"""

import serial
from threading import Thread
import time
from serial.tools import list_ports
from serial import SerialException
import re
import numpy as np


from pydaqs.base import _BaseDAQ
from axopy.daq import _Sleeper



class ArduinoMKR_DAQ(_BaseDAQ):
    
    def __init__(self,
                 rate = 50,
                 baudrate = 57600,
                 samples_per_read = 10,
                 port = None):
        self.baudrate = baudrate
        self.rate = rate
        self.samples_per_read=samples_per_read
        self.port=port
        self._newData = False
        self.buffer_string = ''
        
        # If port is not given find the Arduino one
        if self.port is None:
            self.port = self.get_arduino_port()
        self.sleeper = _Sleeper(1/(self.rate*2)) #multiply by 2 to reduce the sleep period, because of the inaccuracy of the sleeper
            
        
    def __del__(self):
        """Call stop() on destruct."""
        self.stop()    

        
    def get_arduino_port(self):
        device = None
        comports = list_ports.comports()
        for port in comports:
            if port.description.startswith('Arduino MKR'):
                device = port.device
        if device is None:
            raise Exception("Arduino COM port not found.")
        else:
            return device
        
    def start(self):
        #open the serial port
        self.ser = serial.Serial(self.port, self.baudrate) 
        self._flag = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        
    def _run(self):
        while self._flag:
            try:
                # Read all bytes from the serial port and record the data on
                # the last line, which is the latest data uploaded from the 
                # Arduino.
                # The _newData flag turns true to indicate the update of the
                # data
                if self.ser.inWaiting()>10: #only read data larger than 10 bits to avoid empty data
                    # self.buffer_string = self.buffer_string + self.ser.read(self.ser.inWaiting()).decode("utf-8") 
                    self.buffer_string = self.buffer_string + self.ser.read(10).decode("utf-8") 
                    if '\n' in self.buffer_string:
                        lines = self.buffer_string.split('\n') # Guaranteed to have at least 2 entries
                        self.stream = lines[-2]
                        self.buffer_string = lines[-1] #keep the remaining content in the next buffer_string
                        self._newData = True
                    time.sleep(5e-5)  #small delay to avoid CPU running at 100% (still high)
            except (AttributeError, TypeError, SerialException, OSError):
                # this way we can kill the thread by setting the board object
                # to None, or when the serial port is closed by board.exit()
                break
            except Exception as e:
                # catch 'error: Bad file descriptor'
                # iterate may be called while the serial port is being closed,
                # causing an "error: (9, 'Bad file descriptor')"
                if getattr(e, "errno", None) == 9:
                    break
                try:
                    if e[0] == 9:
                        break
                except (IndexError):
                    pass
                raise
                
    def stop(self):
        self._flag = False
        self.ser.close()
        
    def read(self):
        # When new data received, append it to the data array and export the 
        # array when the number of samples reaches the samples_per_read
        # data[i,j]:
        # i : number of channels
        # j : number of sample
        if self._flag:       
            data = []
            while len(data) < self.samples_per_read:
                if self._newData: 
                    try:
                        signal = re.findall(r"[-+]?\d*\.\d+|\d+", self.stream)
                        data.append(signal)
                    except IndexError:
                        pass
                    self._newData= False
                    #time.sleep(1/self.rate) 
                self.sleeper.sleep()
            data=np.array(data) #convert serial string to array  
            data=data.astype(np.float).T #to match the data format for axopy
            return data
        else:
            raise SerialException("Serial port is closed.")
            

if __name__ == '__main__':
    daq = ArduinoMKR_DAQ(samples_per_read = 1)
    daq.start()
    time.sleep(2)
    
    t=0
    Tstart = time.time()
    while time.time()-Tstart<10:
        dat = daq.read()
        t=t+1
        print(dat)