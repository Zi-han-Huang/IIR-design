import cv2
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import matplotlib.animation as animation
import webcam2rgb_modify






class RealtimePlotWindow:

    def __init__(self, channel: str):
        global show
        self.smaple_time=[0,0,0]
        
        # create a plot window
        self.fig, (self.ax, self.ax2,self.ax3) = plt.subplots(3)
        self.pic=self.ax3.imshow(np.zeros((300,400),dtype=np.uint8)*120)
        self.ax3.set_title("Camera preview")
        self.ax.set_title('Original data') 
        # that's our plotbuffer
        self.plotbuffer = np.zeros(100)
        # create an empty line
        self.line, = self.ax.plot(self.plotbuffer,color="green")
        # axis
        self.ax.set_ylim(0, 1)
        # That's our ringbuffer which accumluates the samples
        # It's emptied every time when the plot window below
        # does a repaint
        self.ringbuffer = []

        #Do the same configure as above to set ax2
        self.plotbuffer2 = np.zeros(100)
        self.line2, = self.ax2.plot(self.plotbuffer2,color="red")
        self.ringbuffer2 = []


        
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=100)

        #Set more space to place the titles 
        plt.subplots_adjust(hspace=1)
        self.ax2.text(0.5, -0.5, '*Please tap the camera (not too hard)', horizontalalignment='center', verticalalignment='center', transform=self.ax2.transAxes,color="orange")
    # updates the plot
    def update(self, data):
        
        now_time=time.time()
        self.smaple_time.append(now_time)
        del self.smaple_time[0]
   
        # add new data to the buffer
        self.plotbuffer = np.append(self.plotbuffer, self.ringbuffer)
        # only keep the 100 newest ones and discard the old ones
        self.plotbuffer = self.plotbuffer[-100:]
        self.ringbuffer = []
        # set the new 100 points of channel 9

        #self.line.set_xdata(times)
        self.line.set_ydata(self.plotbuffer)


        self.ax.set_ylim(min(self.plotbuffer)-0.3, max(self.plotbuffer)+0.3)
        #print(time.time())




        # add new data to the buffer
        self.plotbuffer2 = np.append(self.plotbuffer2, self.ringbuffer2)
        # only keep the 100 newest ones and discard the old ones
        self.plotbuffer2 = self.plotbuffer2[-100:]
        self.ringbuffer2 = []
        # set the new 100 points of channel 9

        #self.line.set_xdata(times)
        self.line2.set_ydata(self.plotbuffer2)


        self.ax2.set_ylim(min(self.plotbuffer2)-0.3, max(self.plotbuffer2)+0.3)

        
        return self.line,self.line2

    # appends data to the ringbuffer
    def addData(self, v):
        self.ringbuffer.append(v)


    def addData2(self, v):
        self.ringbuffer2.append(v)
        
    def setAx2Title(self,title,camera_real_fps):
       self.ax2.set_title(title+"\nData refresh rate: "+str(camera_real_fps)+" FPS")
       
    def setAx1Title(self,title):
       self.ax.set_title(title)
       
class IIR_Filter:

    def __init__(self,s):
        #Set coefficient
        self.b=[s[0],s[1],s[2]]
        self.a=[s[4],s[5]]
        
        self.x=[0,0,0]
        self.y=[0,0,0]

          
    def dofilter(self,input_single):
                self.x.insert(0,input_single)
                del self.x[-1]
                
                #Formula for calculating second-order IIR filter  
                yn=self.b[0]*self.x[0]+self.b[1]*self.x[1]+self.b[2]*self.x[2]-self.a[0]*self.y[0]-self.a[1]*self.y[1]

                self.y.insert(0,yn)
                del self.y[-1]

                return yn


class Cascade_IIR:


    def __init__(self,N, cutoff_low,cutoff_high,cam_fs):

        #Calculate coefficients of IIR
        self.N=N
        #Cut off frequency low
        wstart = 2*cutoff_low/cam_fs
        #Cut off frequency high
        wstop=2*cutoff_high/cam_fs
        self.sos= signal.butter(N, [wstart,wstop], 'bandpass',output='sos')

        #Set buffer to calculate time spend between two peaks
        self.peaks_time_list=[0,0,0,0,0]
        self.peaks_list=[0,0,0]

        #list of IIR filter
        self.cascade=[]
        for s in self.sos:
            self.cascade.append(IIR_Filter(s))

    #Do filter one by one
    def doCascadeFilter(self,v):
        for f in self.cascade:
            v=f.dofilter(v)
        return v


    #Use time difference to calculate heart rate
    def calculate_peaks(self,data):
        fs=0
        self.peaks_list.append(data)
        del self.peaks_list[0]
        #check peaks
        if(self.peaks_list[1]>self.peaks_list[0] and self.peaks_list[1]>self.peaks_list[2] ):
            
            peak_time=time.time()
            self.peaks_time_list.append(peak_time)
            del self.peaks_time_list[0]
            
            average_time=(self.peaks_time_list[-1]-self.peaks_time_list[0])/4
            fs=1/average_time
        return fs*60



# The callback function for webcam2rgb
# Note: The parameter data passed in here is the image of the whole frame of the camera,
# Not the data of one point
# The webcam2rgb has been changed to fixed the exposure duration of the camera to about 30ms,  ensure the sampling  rate is 30fps
class Data_receiver:

    
    def __init__(self):
        self.last_time=[1,0,0,0,0,0,0,0,0,0]
    def hasdata(self,retval,data):

          
            now_time=time.time()  
            camera_real_fps=1/((self.last_time[-1]-self.last_time[0])/9)
            self.last_time.append(now_time)
            del self.last_time[0]
        
            
            blue=data[:,:,0]
            blue=np.mean(blue)
            green=data[:,:,1]
            green=np.mean(green)
            red=data[:,:,2]
            red=np.mean(red)
            
            #If red color strong enough, we thought the finger is on the camera
            #If finger is  not on camera, set data to 0
            if not (red>blue+green-15):
                red=0
                realtimePlotWindowRed.setAx2Title("After IIR \n Please put finger on camera ",round(camera_real_fps,2))
            #Plot original data  
            realtimePlotWindowRed.addData(red)

            #Do IIR filter
            result=my_fileter.doCascadeFilter(red)

            #Plot result data
            realtimePlotWindowRed.addData2(result)

            #Calculate heart rate
            heartRate=my_fileter.calculate_peaks(result)

            #Refresh data on the picture
            if(heartRate):
                realtimePlotWindowRed.setAx2Title("After IIR \nHeart rate : "+str(round(heartRate,1)),round(camera_real_fps,2))
            
            realtimePlotWindowRed.pic.set_data( cv2.cvtColor(data, cv2.COLOR_BGR2RGB) )
   
if __name__=="__main__":
    #Create animation 
    realtimePlotWindowRed = RealtimePlotWindow("After IIR")

    camera = webcam2rgb_modify.Webcam2rgb()

    data_receiver=Data_receiver()
    camera.start(callback = data_receiver.hasdata, cameraNumber=0)
    print("camera samplerate: ", camera.cameraFs(), "Hz")


    #Create list of IIR filter
    #After many attempts, I think the following coefficient is the most appropriate

    my_fileter=Cascade_IIR(4,1,2.4,camera.cameraFs())


    print("create my_filter")
    realtimePlotWindowRed.setAx1Title("Original signal")






    plt.show()
    camera.stop()
    print('finished')





