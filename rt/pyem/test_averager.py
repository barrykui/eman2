#!/usr/bin/env    python

from EMAN2 import *
import unittest,os,sys
from test import test_support
import testlib
from pyemtbx.exceptions import *

class TestAverager(unittest.TestCase):
    """averager test"""
    
    def test_ImageAverager(self):
        """test ImageAverager ..............................."""
        
class TestConstructor(unittest.TestCase):
    """constructor test"""
    
    def test_FourierReconstructor(self):
        """test FourierReconstructor ........................"""
        e1 = EMData()
        e1.set_size(32,32,1)
        e1.process_inplace('testimage.noise.uniform.rand')
        e1.do_fft_inplace()
        e2 = EMData()
        e2.set_size(32,32,1)
        e2.process_inplace('testimage.noise.uniform.rand')
        e2.do_fft_inplace()
        e3 = EMData()
        e3.set_size(32,32,1)
        e3.process_inplace('testimage.noise.uniform.rand')
        e3.do_fft_inplace()
        
        r = Reconstructors.get('fourier', {'size':10, 'mode':1, 'weight':0.5, 'dlog':2})
        r.setup()
        r.insert_slice(e1, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e2, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e3, Transform3D(EULER_EMAN, 0,0,0))
        result = r.finish()
    
    def test_WienerFourierReconstructor(self):
        """test WienerFourierReconstructor .................."""
        e1 = EMData()
        e1.set_size(32,32,1)
        e1.process_inplace('testimage.noise.uniform.rand')
        e1.do_fft_inplace()
        e2 = EMData()
        e2.set_size(32,32,1)
        e2.process_inplace('testimage.noise.uniform.rand')
        e2.do_fft_inplace()
        e3 = EMData()
        e3.set_size(32,32,1)
        e3.process_inplace('testimage.noise.uniform.rand')
        e3.do_fft_inplace()
        
        r = Reconstructors.get('wiener_fourier', {'size':10, 'mode':1, 'padratio':0.5, 'snr':(0.2, 3.4, 5.6)})
        r.setup()
        r.insert_slice(e1, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e2, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e3, Transform3D(EULER_EMAN, 0,0,0))
        result = r.finish()
        
    def test_BackProjectionReconstructor(self):
        """test BackProjectionReconstructor ................."""
        e1 = EMData()
        e1.set_size(32,32,1)
        e1.process_inplace('testimage.noise.uniform.rand')
        e2 = EMData()
        e2.set_size(32,32,1)
        e2.process_inplace('testimage.noise.uniform.rand')
        e3 = EMData()
        e3.set_size(32,32,1)
        e3.process_inplace('testimage.noise.uniform.rand')
        
        r = Reconstructors.get('back_projection', {'size':32, 'weight':0.8})
        r.setup()
        r.insert_slice(e1, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e2, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e3, Transform3D(EULER_EMAN, 0,0,0))
        result = r.finish()
        
    def no_test_nn4Reconstructor(self):
        """test nn4Reconstructor ............................"""
        e1 = EMData()
        e1.set_size(34,32,32)
        e1.process_inplace('testimage.noise.uniform.rand')
        e2 = EMData()
        e2.set_size(34,32,32)
        e2.process_inplace('testimage.noise.uniform.rand')
        e3 = EMData()
        e3.set_size(34,32,32)
        e3.process_inplace('testimage.noise.uniform.rand')
        
        Log.logger().set_level(-1)    #no log message printed out
        r = Reconstructors.get('nn4', {'size':32, 'npad':1, 'symmetry':'CSYM'})
        r.setup()
        r.insert_slice(e1, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e2, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e3, Transform3D(EULER_EMAN, 0,0,0))
        result = r.finish()
   
    def no_test_ReverseGriddingReconstructor(self):
        """test ReverseGriddingReconstructor ................"""
        e1 = EMData()
        e1.set_size(32,32,1)
        e1.process_inplace('testimage.noise.uniform.rand')
        e2 = EMData()
        e2.set_size(32,32,1)
        e2.process_inplace('testimage.noise.uniform.rand')
        e3 = EMData()
        e3.set_size(32,32,1)
        e3.process_inplace('testimage.noise.uniform.rand')
        
        r = Reconstructors.get('reverse_gridding', {'size':32, 'weight':0.8, 'npad':1})
        r.setup()
        r.insert_slice(e1, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e2, Transform3D(EULER_EMAN, 0,0,0))
        r.insert_slice(e3, Transform3D(EULER_EMAN, 0,0,0))
        result = r.finish()

class TestProjector(unittest.TestCase):
    """test Projector"""
    
    def test_GaussFFTProjector(self):
        """test GaussFFTProjector ..........................."""
        e = EMData()
        e.set_size(32,32,32)
        e.process_inplace('testimage.noise.uniform.rand')
        
        e.project('gauss_fft', {'alt':1.234, 'az':1.345, 'phi':1.54, 'mode':1})

        
def test_main():
    test_support.run_unittest(TestAverager, TestConstructor, TestProjector)

if __name__ == '__main__':
    test_main()