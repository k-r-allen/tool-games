from __future__ import division, print_function
from builtins import super
import os
import sys
import unittest
import json
import copy
import pdb

from pyGameWorld import *
from pyGameWorld.viewer import *


BASIC_WORLD_LOC = os.path.join(os.path.dirname(__file__),
                               "unittest_files", "basic_world.json")

BASIC_TP_LOC = os.path.join(os.path.dirname(__file__),
                            "unittest_files", "basic_toolpicker.json")

with open(BASIC_WORLD_LOC, 'r') as wfl:
    bw_dict = json.load(wfl)

with open(BASIC_TP_LOC, 'r') as wfl:
    btp_dict = json.load(wfl)

WINNING_BASIC_POS = [85, 400]
WINNING_TIME = 7.1
NEARMISS_BASIC_POS = [85, 440]
COLLIDE_POS = [130, 80]
AWFUL_POSITION = [500, 100]

def make_action_from_basic_tp(obj, pos):
    tverts = btp_dict['tools'][obj]
    nverts = [[[v[0] + pos[0], v[1] + pos[1]] for v in verts] for
              verts in tverts]
    def act(world, data):
        world['objects']['PLACED'] = {
            'type': 'Compound',
            'color': 'blue',
            'density': 1,
            'polys': nverts
        }
        #pdb.set_trace()
        return world
    return Action(act, "Test action")

def approxeq(x, y, tol=0.001):
    return abs(x-y) < tol

class BasicWorldSetup(unittest.TestCase):
    def setUp(self):
        self.worlddict = bw_dict
        self.world = loadFromDict(self.worlddict)

class BasicWorldTest(BasicWorldSetup):
    def test_runnable(self):
        def getresp():
            self.world.step(10.)
            return self.world.checkEnd()
        self.assertFalse(getresp(), 'Running static world returns goal hit')


class JSRunTest(BasicWorldSetup):
    def setUp(self):
        super().setUp()
        self.ctx = JSRunner()
        self.win_world = copy.deepcopy(self.worlddict)

    def test_basicrun(self):
        isin, tm = self.ctx.run_gw(self.worlddict, 20)
        self.assertFalse(isin, "Running static world returns goal hit")
        self.assertTrue(tm > 20, "World stopped before end point")


class ToolPickerTest(BasicWorldSetup):
    def setUp(self):
        super().setUp()
        self.tpdict = btp_dict
        self.tp = ToolPicker(self.tpdict)

    def test_placement_collision(self):
        self.assertTrue(self.tp.checkPlacementCollide('obj3', COLLIDE_POS),
                        "Did not catch placement collision")
        self.assertFalse(self.tp.checkPlacementCollide('obj2', NEARMISS_BASIC_POS),
                         "Found placement collision that does not exist")

    def test_good_placement(self):
        ret, tm = self.tp.runPlacement('obj1', WINNING_BASIC_POS)
        self.assertTrue(ret, "Did not find valid solution")
        self.assertTrue(approxeq(tm, WINNING_TIME),
                        "Did not solve in the right time ("+str(WINNING_TIME)+
                        "s)")

    def test_bad_placement(self):
        ret, tm = self.tp.runPlacement('obj1', NEARMISS_BASIC_POS)
        self.assertFalse(ret, "Found invalid solution")
        self.assertTrue(tm > 20., "Bad placement stopped early")

if __name__ == '__main__':
    unittest.main()
