# unitary test for the RedPitaya and Pyrpl modules and baseclass for all other
# tests
import logging
logger = logging.getLogger(name=__name__)
import os
from .. import Pyrpl, user_config_dir, global_config
from ..pyrpl_utils import time
from ..async_utils import sleep as async_sleep
from ..errors import UnexpectedPyrplError, ExpectedPyrplError

# I don't know why, in nosetests, the logger goes to UNSET...
logger_quamash = logging.getLogger(name='quamash')
logger_quamash.setLevel(logging.INFO)

class TestPyrpl(object):
    """ base class for all pyrpl tests """
    # names of the configfiles to use
    source_config_file = "nosetests_source.yml"
    tmp_config_file = "nosetests_config.yml"

    @classmethod
    def erase_temp_file(self):
        tmp_conf = os.path.join(user_config_dir,
                     self.tmp_config_file)
        if os.path.isfile(tmp_conf):
            try:
                os.remove(tmp_conf)
            # sometimes, an earlier test delete file between exists and
            # remove calls, this gives a WindowsError
            except WindowsError:
                pass
        while os.path.exists(tmp_conf):
            pass  # make sure the file is really gone before proceeding further

    @classmethod
    def setUpAll(cls):
        print("=======SETTING UP %s=============" % cls.__name__)
        # these tests will not succeed without the hardware
        cls.erase_temp_file()  # also before (for instance in case of Ctrl-C)
        cls.pyrpl = Pyrpl(config=cls.tmp_config_file,
                          source=cls.source_config_file)
        # self.pyrpl.create_widget() # create a second widget to be sure
        cls.r = cls.pyrpl.rp
        # get an estimate of the read/write time
        N = 10
        t0 = time()
        for i in range(N):
            cls.r.hk.led
        cls.read_time = (time()-t0)/float(N)
        t0 = time()
        for i in range(N):
            cls.r.hk.led = 0
        cls.write_time = (time()-t0)/float(N)
        cls.communication_time = (cls.read_time + cls.write_time)/2.0
        print("Estimated time per read / write operation: %.1f ms / %.1f ms" %
              (cls.read_time*1000.0, cls.write_time*1000.0))
        async_sleep(0.1)  # give some time for events to get processed


    def test_read_write_time(self):
        # maximum time per read/write in seconds
        try:
            maxtime = global_config.test.max_communication_time
        except:
            raise ExpectedPyrplError("Error with global config file. "
                                       "Please delete the file %s and retry!"
                                       % os.path.join(user_config_dir,
                                                      'global_config.yml'))
        assert self.read_time < maxtime, \
            "Read operation is very slow: %e s (expected < %e s). It is " \
            "highly recommended that you improve the network connection to " \
            "your Red Pitaya device. " % (self.read_time, maxtime)
        assert self.write_time < maxtime, \
            "Write operation is very slow: %e s (expected < %e s). It is " \
            "highly recommended that you improve the network connection to " \
            "your Red Pitaya device. " % (self.write_time, maxtime)

    @classmethod
    def tearDownAll(cls):
        print("=======TEARING DOWN %s===========" % cls.__name__)
        # shut down Pyrpl
        cls.pyrpl._clear()
        async_sleep(0.1)  # give some time for events to get processed
        # delete the configfile
        cls.erase_temp_file()

    def test_pyrpl(self):
        assert (self.pyrpl is not None)

# only one test class per file is allowed due to conflicts
