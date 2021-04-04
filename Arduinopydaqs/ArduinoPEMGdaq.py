# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 21:30:10 2021

@author: Hancong Wu
"""
import serial
from threading import Thread
import time
from serial.tools import list_ports
from serial import SerialException
import re
import numpy as np
from struct import calcsize,pack,unpack


from pydaqs.base import _BaseDAQ
from axopy.daq import _Sleeper



class ArduinoMKR_DAQ(_BaseDAQ):
    
    def __init__(self,
                 rate = 50,
                 baudrate = 57600,
                 samples_per_read = 10,
                 mode = 'measure',
                 ctrl = None, #only use when switching the controller
                 port = None):
        self.baudrate = baudrate
        self.rate = rate
        self.samples_per_read=samples_per_read
        self.mode = mode
        self.port=port
        self.ctrl=ctrl
        self._newData = False
        
        if self.mode == 'calibration':
            self.data_type = '<ffc' # Format to match arduino struct
        elif self.mode == 'calibration_low':
            self.data_type = '<ffc' # Format to match arduino struct
        elif self.mode == 'visualization':
            self.data_type = '<ffffc' # Format to match arduino struct
        elif self.mode == 'measure':
            self.data_type = '<ffhhhfc' # Format to match arduino struct
        self.data_size = calcsize(self.data_type)

        
        # If port is not given find the Arduino one
        if self.port is None:
            self.port = self.get_arduino_port()
        self.sleeper = _Sleeper(1/(self.rate*5))
            
        
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
        time.sleep(0.5)
        #select mode
        if self.mode == 'calibration':
            self.ser.write(b'CLC') 
        elif self.mode == 'calibration_low':
            self.ser.write(b'CLR')
        elif self.mode == 'visualization':
            self.ser.write(b'CLV')
        elif self.mode == 'measure':
            self.ser.write(b'MEA')
            
        time.sleep(0.1) #allow arduino to finish the previous data transfer
  
        #flush the buffer to ensure the data are in the same format
        self.ser.flushInput() 
        #use the marker to find the starting point of the data
        end_marker = b'a'
        pointer = b''
        while pointer!=end_marker:
            pointer =self.ser.read()
        
        self._flag = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
    
    #set the controller on the Arduino PEMG system
    def setArduino(self):
        #open the serial port
        self.ser = serial.Serial(self.port, self.baudrate)
        time.sleep(0.5)
                
        if self.ctrl == 'abstract_ctrl':
            self.ser.write(b'CF1') 
        elif self.ctrl == 'direct_ctrl':
            self.ser.write(b'CF2')
        elif self.ctrl == 'LDA_ctrl':
            self.ser.write(b'CF3')
            
        print('The controller has been switched to:',self.ctrl)
        self.stop()
        
        
    def readCalibration(self):
        #open the serial port
        self.ser = serial.Serial(self.port, self.baudrate)
        time.sleep(0.5)
        
        
        self.ser.write(b'RCAL') 
        time.sleep(0.5)
        self.ser.flushInput() 
        
        buffer = ''
        Flag = True
        while Flag:
        
            if self.ser.in_waiting > 0:
                buffer += self.ser.read(self.ser.in_waiting).decode("utf-8") 
                Flag = False
            
        self.stop()
        return buffer
        
    def _run(self):
        while self._flag:
            try:
                # Read all bytes from the serial port and record the data on
                # the last line, which is the latest data uploaded from the 
                # Arduino.
                # The _newData flag turns true to indicate the update of the
                # data
                if self.ser.inWaiting()>=self.data_size:
                    self.byteData = self.ser.read(self.data_size)
                    self.unpackedData = unpack(self.data_type, self.byteData)
                    self._newData = True
                    time.sleep(1e-6) #small delay to avoid CPU running at 100% 
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
        # try:
        #     self.ser.close()
        # except NameError:
        #     pass
        if "self.ser" in locals():
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
                        
                        data.append(self.unpackedData)
                    except IndexError:
                        pass
                    self._newData= False
                time.sleep(1e-6) 
                # self.sleeper.sleep()
            data=np.array(data) #convert serial string to array 
            data = data[:self.samples_per_read,:(len(data[0])-1)] #remove the end marker
            data=data.astype(np.float).T #to match the data format for axopy
            return data
        else:
            raise SerialException("Serial port is closed.")
            

if __name__ == '__main__':
    
    # #select a controller
    # daq = ArduinoMKR_DAQ(ctrl = 'abstract_ctrl')
    # daq.setArduino()
    # time.sleep(1)
    
    # daq = ArduinoMKR_DAQ(samples_per_read = 50,rate = 500, mode = 'calibration')
    daq = ArduinoMKR_DAQ(samples_per_read = 50,rate = 500, mode = 'visualization')
    # daq = ArduinoMKR_DAQ(samples_per_read = 1)

    daq.start()
    time.sleep(1)
    
    t=0
    Tstart = time.time()
    while time.time()-Tstart<8:
        dat = daq.read()
        t=t+1
        print(dat)
    daq.stop()    
    
    
    # dat = daq.read()
    # print(dat)
