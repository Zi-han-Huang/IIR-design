import unittest
from scipy import signal
import numpy as  np
from realtime_iir_main import IIR_Filter,Cascade_IIR





class IIRfir_test(unittest.TestCase):
 ## test for 2nd order iir filter：

    def test_IIRfilter(self):
        print("test_IIRfilter")
        fs=30
        fl=1
        fh=2
        wstart = 2 * fl / fs
        wstop = 2 * fh / fs
        sos = signal.butter(1, [wstart, wstop], 'bandpass', output='sos') # iir filter coefficients
        s=np.reshape(sos,-1)

        input = np.array([1, 2,  0, 1.5, 5, 6, 4, 2])  # set up the input for testing
        expected_output = signal.sosfilt(sos, input) ### calculate expected output of the filter
        expected_output.tolist()

        real_output = []
        iir = IIR_Filter(s)# setup for iir filter
        input.tolist()
        for i in input:
            real_output.append(iir.dofilter(i))  # result from the iir filter


        for i in range(0, len(input)):
         self.assertAlmostEqual(real_output[i],expected_output[i],14) # verify the result for every output
## test for chain of 2nd iir filter

    def test_chain(self):
        print("test_chain")
        fs = 30
        fl = 1
        fh = 2
        wstart = 2 * fl / fs
        wstop = 2 * fh / fs
        sos = signal.butter(4, [wstart, wstop], 'bandpass', output='sos')  # iir filter coefficients
        input = np.array([1, 2,  0, 1.5, 5, 6, 4, 2])
        expected_output = signal.sosfilt(sos, input) # expected output of the filter.
        expected_output.tolist()
        real_output = []
        iir = Cascade_IIR(4, fl, fh, fs) # setup for chain of iir filter
        input.tolist()
        for i in input:
          real_output.append(iir.doCascadeFilter(i)) # result from chain of iir filter in main code


        for i in range(0, len(input)):
           self.assertAlmostEqual(real_output[i], expected_output[i], 14) # verify the result for every output


if __name__=="__main__":
    unittest.main(verbosity=2)
    
