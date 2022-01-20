# the version without filter

# !/usr/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import signal
import time
import webcam2rgb
import cv2


class RealtimePlotWindow:

    def __init__(self, channel: str):
        # create a plot window
        self.fig, (self.ax, self.ax_iir) = plt.subplots(2)
        self.ax.set_title('Original data')
        self.ax_iir.set_title('After filtering')
        #ax.plt.title("Oiginal")
        # that's our plotbuffer
        self.plotbuffer = np.zeros(50)
        self.plotbuffer_iir = np.zeros(50)
        # create an empty line
        self.line, = self.ax.plot(self.plotbuffer)
        self.line_iir, = self.ax_iir.plot(self.plotbuffer_iir)
        # axis
        # That's our ringbuffer which accumluates the samples
        # It's emptied every time when the plot window below
        # does a repaint
        self.ringbuffer = []
        self.ringbuffer_iir = []
        # add any initialisation code here (filters etc)
        # start the animation
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=100)
        # adjust the space between two subplots
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.5, hspace=0.5)

    # updates the plot
    def update(self, data):
        # add new data to the buffer
        self.plotbuffer = np.append(self.plotbuffer, self.ringbuffer)
        self.plotbuffer_iir = np.append(self.plotbuffer_iir, self.ringbuffer_iir)
        # only keep the 50 newest ones and discard the old ones
        self.plotbuffer = self.plotbuffer[-50:]
        self.plotbuffer_iir = self.plotbuffer_iir[-50:]
        self.ringbuffer = []
        self.ringbuffer_iir = []
        # set the new 50 points of channel 9
        self.line.set_ydata(self.plotbuffer)
        self.line_iir.set_ydata(self.plotbuffer_iir)
        # set the y axis limit
        self.ax.set_ylim(-255, 255)
        self.ax_iir.set_ylim(-255, 255)
        return self.line, self.line_iir

    # appends data to the ringbuffer
    def addData(self, v):
        self.ringbuffer.append(v)

    def addData_iir(self, v):
        self.ringbuffer_iir.append(v)

    def addTitle(self, sampling_rate):
        self.ax.set_title('Original data\n'+"Real time sampling rate: "+str(sampling_rate)+" FPS")

    def addTitle_iir(self, result_iir):
        self.ax_iir.set_title('After filtering\n'+"fan speed after filtering : " + str(result_iir))


class IIR2_filter:

    def __init__(self, s):
        self.b0 = s[0]
        self.b1 = s[1]
        self.b2 = s[2]
        self.a1 = s[4]
        self.a2 = s[5]
        self.buffer1 = 0
        self.buffer2 = 0

    def filter(self, value):
        inputt = value
        inputt = inputt - (self.a1 * self.buffer1)
        inputt = inputt - (self.a2 * self.buffer2)

        output = inputt * self.b0
        output = output + (self.b1 * self.buffer1)
        output = output + (self.b2 * self.buffer2)

        self.buffer2 = self.buffer1
        self.buffer1 = inputt

        return output


class IIR_filter:
    def __init__(self, sos):
        self.cascade = []
        for s in sos:
            self.cascade.append(IIR2_filter(s))

    def dofilter(self, value):
        for f in self.cascade:
            value = f.filter(value)
        return value


# calculate the speeed of the fan
last_status = 0
last_peak_time = 0


def calFanSpeed(data):
    global last_status, last_peak_time
    fan_speed = 0
    peak_rate = 0
    # if the data surpass the threshold value, count as a peak
    if data > 10:
        peak = 1
    else:
        peak = 0
    # Detect falling edge of a peak
    cur_status = peak
    if cur_status == 0 and last_status == 1:
        # Calculating the time interval between the two peaks to obtain the peak_rate 
        cur_peak_time = time.time() 
        if last_peak_time != 0:
            peak_rate = 60 / (cur_peak_time - last_peak_time)
        last_peak_time = cur_peak_time

    last_status = cur_status
    # Because there are six blades, the speed of the fan should be 1/6 of the peak rate
    fan_speed = peak_rate / 6
    return fan_speed


# create callback method reading camera and plotting in windows
i = 0
list_result=[]
list_time=[]
def hasData(retval, data):
    result = 0
    global i,list_result,list_time
    r = data[2]
    # plot the original figure
    realtimePlotWindowRed.addData(r)

    # plot the figure after filtering
    r_iir = iir_filter.dofilter(r)
    realtimePlotWindowRed.addData_iir(r_iir)

    result_iir = calFanSpeed(r_iir)
    if result_iir:
        list_result.append(result_iir)

    # check the sampling rate by obtaining the time gap of every callback
    time_cur = time.time()
    list_time.append(time_cur)
    time_last = time_cur
    
    # The results of fan speed and sampling rate are averaged to obtain a more stable output
    i += 1
    if i > 30 and list_result:
        avg=np.mean(list_result)
        print("\nfan speed after IIR: ", int(avg), "rpm")
        realtimePlotWindowRed.addTitle_iir(int(avg))

        sampling_rate=1/((list_time[-1]-list_time[0])/(len(list_time)-1))
        # Output sampling rate with two decimal places
        print("check sampling rate", format(sampling_rate, '.2f'))
        realtimePlotWindowRed.addTitle(format(sampling_rate, '.2f'))
        
        i = 0
        list_result=[]
        list_time=[]
        
realtimePlotWindowRed = RealtimePlotWindow("red")
# create instances of camera
camera = webcam2rgb.Webcam2rgb()
# Add a horizontal line as the reference line for the threshold
plt.axhline(y=10, ls=":", c="red")
# start the thread and stop it when we close the plot windows
camera.start(callback=hasData, cameraNumber=0)
# create instances for iir filter
wc1 = 2 * 0.5 / camera.cameraFs()
wc2 = 2 * 5 / camera.cameraFs()
sos = signal.butter(3, [wc1, wc2], 'bandpass', output='sos')
iir_filter = IIR_filter(sos)
print("camera samplerate: ", camera.cameraFs(), "Hz")
plt.show()
camera.stop()
# shutdown the camera
camera.cam.release()
cv2.destroyAllWindows()
print('finished')



