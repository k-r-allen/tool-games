import numpy as np
from .constants import *
from .object import *

__all__ = ["PGCond_AnyInGoal", "PGCond_SpecificInGoal", "PGCond_AnyTouch",
           "PGCond_SpecificTouch", "PGCond_ManyInGoal"]

class PGCond_Base(object):

    def __init__(self):
        self.goal = self.obj = self.parent = self.dur = None

    def _getTimeIn(self):
        return -1

    def remainingTime(self):
        ti = self._getTimeIn()
        if ti == -1:
            return None
        curtime = self.parent.time - ti
        return max(self.dur - curtime, 0)

    def isWon(self):
        return self.remainingTime() == 0

    def attachHooks(self):
        raise NotImplementedError("Cannot attach hooks from base condition object")


class PGCond_AnyInGoal(PGCond_Base):

    def __init__(self, goalname, duration, parent, exclusions = []):
        self.type = "AnyInGoal"
        self.won = False
        self.goal = goalname
        self.excl = exclusions
        self.dur = duration
        self.ins = {}
        self.hasTime = True
        self.parent = parent

    def _goesIn(self, obj, goal):
        if (goal.name == self.goal and \
                    (not obj.name in self.ins.keys()) and \
                    (not obj.name in self.excl)):
            self.ins[obj.name] = self.parent.time

    def _goesOut(self, obj, goal):
        if (goal.name == self.goal and \
            obj.name in self.ins.keys() and \
                    (not goal.pointIn(obj.position))):
            del self.ins[obj.name]

    def attachHooks(self):
        self.parent.setGoalCollisionBegin(self._goesIn)
        self.parent.setGoalCollisionEnd(self._goesOut)

    def _getTimeIn(self):
        if len(self.ins) == 0:
            return -1
        mintime = min(min(self.ins.values()), self.parent.time)
        return mintime

class PGCond_ManyInGoal(PGCond_Base):

    def __init__(self, goalname, objlist, duration, parent):
        self.type = "ManyInGoal"
        self.won = False
        self.goal = goalname
        self.objlist = objlist
        self.objsin = []
        self.dur = duration
        self.tin = -1
        self.hasTime = True
        self.parent = parent

    def _goesIn(self, obj, goal):
        if (goal.name == self.goal and
            obj.name in self.objlist and
            obj.name not in self.objsin):
            self.objsin.append(obj.name)
            if len(self.objsin) == 1:
                self.tin = self.parent.time

    def _goesOut(self, obj, goal):
        if (goal.name == self.goal and
            obj.name in self.objsin):
            self.objsin.remove(obj.name)
            if len(self.objsin) == 0:
                self.tin = -1

    def attachHooks(self):
        self.parent.setGoalCollisionBegin(self._goesIn)
        self.parent.setGoalCollisionEnd(self._goesOut)

    def _getTimeIn(self):
        return self.tin


class PGCond_SpecificInGoal(PGCond_Base):

    def __init__(self, goalname, objname, duration, parent):
        self.type = "SpecificInGoal"
        self.won = False
        self.goal = goalname
        self.obj = objname
        self.dur = duration
        self.tin = -1
        self.hasTime = True
        self.parent = parent

    def _goesIn(self, obj, goal):
        if goal.name == self.goal and obj.name == self.obj:
            self.tin = self.parent.time

    def _goesOut(self, obj, goal):
        if goal.name == self.goal and obj.name == self.obj and (not goal.pointIn(obj.position)):
            self.tin = -1

    def attachHooks(self):
        self.parent.setGoalCollisionBegin(self._goesIn)
        self.parent.setGoalCollisionEnd(self._goesOut)

    def _getTimeIn(self):
        return self.tin


class PGCond_AnyTouch(PGCond_Base):

    def __init__(self, objname, duration, parent):
        self.type = "AnyTouch"
        self.won = False
        self.goal = objname
        self.dur = duration
        self.tin = -1
        self.hasTime = True
        self.parent = parent

    def _beginTouch(self, obj, goal):
        if obj.name == self.goal or goal.name == self.goal:
            self.tin = self.parent.time

    def _endTouch(self, obj, goal):
        if obj.name == self.goal or goal.name == self.goal:
            sefl.tin = -1

    def attachHooks(self):
        self.parent.setSolidCollisionBegin(self._beginTouch)
        self.parent.setSolidCollisionEnd(self._endTouch)

    def _getTimeIn(self):
        return self.tin

class PGCond_SpecificTouch(PGCond_Base):

    def __init__(self, objname1, objname2, duration, parent):
        self.type = "SpecificTouch"
        self.won = False
        self.o1 = objname1
        self.o2 = objname2
        self.dur = duration
        self.tin = -1
        self.hasTime = True
        self.parent = parent

    def _beginTouch(self, obj1, obj2):
        if (obj1.name == self.o1 and obj2.name == self.o2) or \
            (obj1.name == self.o2 and obj2.name == self.o1):
            self.tin = self.parent.time

    def _endTouch(self, obj1, obj2):
        if (obj1.name == self.o1 and obj2.name == self.o2) or \
            (obj1.name == self.o2 and obj2.name == self.o1):
            self.tin = -1

    def attachHooks(self):
        self.parent.setSolidCollisionBegin(self._beginTouch)
        self.parent.setSolidCollisionEnd(self._endTouch)

    def _getTimeIn(self):
        return self.tin
