import logging
logger = logging.getLogger(name=__name__)
import os
from ..memory import MemoryTree, MemoryBranch
from .. import *
from ..async_utils import sleep

class TestMemory(object):
    def test_load(self):
        mt = MemoryTree(filename='test', source='nosetests_source')
        assert mt is not None
        assert os.path.isfile(mt._filename)
        mt = MemoryTree()
        assert mt is not None
        assert mt._filename is None
        mt = MemoryTree(source="nosetests_source")
        assert mt is not None
        assert mt._filename is None
        mt = MemoryTree('test')
        assert mt.pyrpl._data is not None
        mt = MemoryTree('test')
        os.remove(mt._filename)
        mt = MemoryTree('test')
        assert len(mt._keys()) == 0
        os.remove(mt._filename)

    def test_usage(self):
        filename = 'test2'
        m = MemoryTree(filename)
        m.a = 1
        assert not isinstance(m.a, MemoryBranch)
        m.b = {}
        assert isinstance(m.b, MemoryBranch)
        m.b = 'fdf'
        assert not isinstance(m.b, MemoryBranch)
        m.c = []
        assert isinstance(m.c, MemoryBranch)
        m.c[0] = 0
        m.c[1] = 2
        assert m.c._pop(-1) == 2
        assert len(m.c) == 1
        m.c[1] = 11
        m.c[2] = 22
        m.c[3] = 33
        assert len(m.c) == 4
        assert m.c._pop(2) == 22
        assert m.c[2] == 33
        # do something tricky
        m.d = dict(e=1,
                   f=dict(g=[0, dict(h=[0,99,98]),{}]))
        assert m.d.f.g[1].h[2]==98
        assert isinstance(m.d.f.g[1].h, MemoryBranch)
        # list addition
        m.x = [1.2]
        assert (m.x+[2.1]) == [1.2, 2.1]
        assert ([3.2]+m.x) == [3.2, 1.2]
        # list addition with strings - used to be a source of bugs
        m.l = ['memory']
        assert (m.l+['list']) == ["memory", "list"]
        assert (['list']+m.l) == ["list", "memory"]
        # read from saved file
        m._save_now()
        m2 = MemoryTree(m._filename)
        assert m.d.f.g[1].h[2] == 98
        assert isinstance(m.d.f.g[1].h, MemoryBranch)
        # save and delete file
        m._save_now()
        os.remove(m._filename)

    def test_two_trees(self):
        """ makes two different memorytree objects that might have conflicts w.r.t. each other.

        The conflicts arise from the latency between the objects in memory and the file defined
        by _loadsavedeadtime for speed reasons.
        """
        filename = 'test3'
        T1, T2 = 0.5, 2.0
        m1 = MemoryTree(filename, _loadsavedeadtime=T1)
        assert m1._loadsavedeadtime == T1
        assert m1._save_counter == 0
        m1.a = 1
        assert m1._save_counter == 1
        m1.b = {'b1': 1, 'b22': 2.2, }
        assert m1._save_counter == 4
        m1._save_now()
        assert m1._save_counter == 5
        m1.a = 2
        assert m1._save_counter == 6
        m2 = MemoryTree(filename, _loadsavedeadtime=T2)
        assert m1._save_counter == 6
        assert m2._loadsavedeadtime == T2
        assert m1._loadsavedeadtime == T1
        assert m1.a == 2
        assert m1._save_counter == 6
        # changes will only be written to file once m1._loadsavedeadtime has elapsed
        assert m2.a == 1, m2.a
        sleep(T1+0.05)  # some extra time is needed for overhead
        # now changes should have been written to file
        assert not m1._savetimer.isActive(), m1._savetimer.interval()
        assert m1._save_counter == 7, m1._save_counter
        # but m2 will only attempt to
        # reload once m2._loadsavedeadtime has elapsed
        assert m2.a == 1
        # once we wait long enough, m2 will attempt to reload the file
        sleep(T2 - T1)
        assert m1._save_counter == 7
        assert m2.a == 2, m2.a
        m2.a = 3
        assert m2.a == 3
        # m1 has also done nothing for a long time, so it will attempt to reload instantaneously
        assert m1.a == 3
        assert m1._save_counter == 7
        # clean up
        m1._save_now()
        m2._save_now()
        os.remove(m1._filename)

    def test_two_trees_nodeadtime(self):
        """ makes two different memorytree objects that might have conflicts w.r.t. each other.

        When _loadsavedeadtime is set to 0, no conflicts are possible since both memorytrees are
        always up to date with the file.
        """
        filename = 'test4'
        T1, T2 = 0.0, 0.0
        m1 = MemoryTree(filename, _loadsavedeadtime=T1)
        assert m1._loadsavedeadtime == T1
        assert m1._save_counter == 0
        m1.a = 1
        assert m1._save_counter == 1
        m1.b = {'b1': 1, 'b22': 2.2, }
        assert m1._save_counter == 4
        m1._save_now()
        assert m1._save_counter == 5
        m1.a = 2
        assert m1._save_counter == 6
        m2 = MemoryTree(filename, _loadsavedeadtime=T2)
        assert m1._save_counter == 6
        assert m2._loadsavedeadtime == T2
        assert m1._loadsavedeadtime == T1
        assert m1.a == 2
        assert m1._save_counter == 6
        assert m2.a == 2, m2.a
        assert not m1._savetimer.isActive(), m1._savetimer.interval()
        assert m1._save_counter == 6, m1._save_counter
        assert m2.a == 2
        assert m1._save_counter == 6
        assert m2.a == 2, m2.a
        m2.a = 3
        assert m2.a == 3
        # m1 has also done nothing for a long time, so it will attempt to reload instantaneously
        assert m1.a == 3
        assert m1._save_counter == 6
        # clean up
        m1.c = 5
        assert m2.c == 5
        m2.c = 6
        m1.c = 7
        assert m2.c == 7
        m1._save_now()
        m2._save_now()
        os.remove(m1._filename)
