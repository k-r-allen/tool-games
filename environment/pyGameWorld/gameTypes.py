from .world import PGWorld, loadFromDict
from .jsrun import *
from .noisyWorld import noisifyWorld
import json, os
import pdb

__all__ = ['ToolPicker','loadToolPicker', 'placeObjectInWorld', 'checkCollisionInWorld',
           'checkCollisionByPolys', 'placeObjectByPolys']

def placeObjectByPolys(world, polys, position):
    if checkCollisionByPolys(world, polys, position):
        return False
    placed = []
    for poly in polys:
        placed.append([(p[0]+position[0], p[1]+position[1]) for p in poly])
    world.addPlacedCompound("PLACED", placed, (0,0,255))
    return world

def placeObjectInWorld(toolpicker, world, toolname, position):
    assert toolname in toolpicker._tools.keys()
    tool = toolpicker._tools[toolname]
    return placeObjectByPolys(world, tool, position)

def checkCollisionByPolys(world, polys, position):
    for pverts in polys:
        if world.checkCollision(position, pverts):
            return True
    return False

def checkCollisionInWorld(toolpicker, world, toolname, position):
    assert toolname in toolpicker._tools.keys()
    tool = toolpicker._tools[toolname]
    return checkCollisionByPolys(world, tool, position)

# Basic game of picking tools and placing them
class ToolPicker(object):
    def __init__(self, gamedict, basicTimestep = 0.1, worldTimestep=1./100.):
        self._world = loadFromDict(gamedict['world'])
        self._worlddict = gamedict['world']
        self.t = 0
        self.bts = basicTimestep
        self.wts = min(basicTimestep, worldTimestep)
        self._world.bts = self.wts
        self._tools = gamedict['tools']

    def checkPlacementCollide(self, toolname, position):
        for tverts in self._tools[toolname]:
            if self._world.checkCollision(position, tverts):
                return True
        return False

    # Determines the outcome from putting an object in the world
    def runPlacement(self, toolname, position, maxtime = 20., useJS = False):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, -1
        tmpWorld = loadFromDict(self._world.toDict())
        tmpWorld.bts = self.wts

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0]+position[0], p[1]+position[1]) for p in poly])

        tmpWorld.addPlacedCompound('PLACED',placeTool,(0,0,255))
        if useJS:
            return jsRunGame(tmpWorld, maxtime, self.bts)
        else:
            return pyRunGame(tmpWorld, maxtime, self.bts)

    def observePlacementPath(self, toolname, position, maxtime = 20., useJS = False):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1
        tmpWorld = loadFromDict(self._world.toDict())
        tmpWorld.bts = self.wts

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0]+position[0], p[1]+position[1]) for p in poly])

        tmpWorld.addPlacedCompound('PLACED',placeTool,(0,0,255))
        if useJS:
            return jsGetPath(tmpWorld, maxtime, self.bts)
        else:
            return pyGetPath(tmpWorld, maxtime, self.bts)

    def observePlacementStatePath(self, toolname, position, maxtime = 20., useJS = False):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1
        tmpWorld = loadFromDict(self._world.toDict())
        tmpWorld.bts = self.wts

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0]+position[0], p[1]+position[1]) for p in poly])

        tmpWorld.addPlacedCompound('PLACED',placeTool,(0,0,255))
        if useJS:
            return jsGetStatePath(tmpWorld, maxtime, self.bts)
        else:
            return pyGetStatePath(tmpWorld, maxtime, self.bts)

    def observeCollisionEvents(self, toolname, position, maxtime = 20., useJS = False, collisionSlop = .2001):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1
        tmpWorld = loadFromDict(self._world.toDict())
        tmpWorld.bts = self.wts

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0]+position[0], p[1]+position[1]) for p in poly])

        tmpWorld.addPlacedCompound('PLACED',placeTool,(0,0,255))
        if useJS:
            return jsGetCollisions(tmpWorld, maxtime, self.bts)
        else:
            return pyGetCollisions(tmpWorld, maxtime, self.bts, collisionSlop)

    # Puts an object in the world permanently
    def placeObject(self, toolname, position):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        if self.checkPlacementCollide(toolname, position):
            return False
        placeTool = []
        for poly in self._tools[toolname]:
            placeTool.append([(p[0] + position[0], p[1] + position[1]) for p in poly])
        self._world.addPlacedCompound('PLACED',placeTool,(0,0,255))
        return True

    # Makes own world noisy
    def noisifySelf(self, noise_position_static = 5., noise_position_moving = 5.,
                 noise_collision_direction = .2, noise_collision_elasticity = .2, noise_gravity = .1,
                 noise_object_friction = .1, noise_object_density = .1, noise_object_elasticity = .1):
        self._world = noisifyWorld(self._world, noise_position_static, noise_position_moving,
                                   noise_collision_direction, noise_collision_elasticity, noise_gravity,
                                   noise_object_friction, noise_object_density, noise_object_elasticity)

    def runNoisyPlacement(self, toolname, position, maxtime = 20., useJS = False,
                          noise_position_static = 5., noise_position_moving = 5.,
                          noise_collision_direction = .2, noise_collision_elasticity = .2, noise_gravity = .1,
                          noise_object_friction = .1, noise_object_density = .1, noise_object_elasticity = .1):

        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        nw = noisifyWorld(loadFromDict(self._worlddict), noise_position_static, noise_position_moving,
                                   noise_collision_direction, noise_collision_elasticity, noise_gravity,
                                   noise_object_friction, noise_object_density, noise_object_elasticity)

        # Make sure the tool can be placed
        for tverts in tool:
            if nw.checkCollision(position, tverts):
                return None, -1

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0] + position[0], p[1] + position[1]) for p in poly])

        nw.addPlacedCompound('PLACED', placeTool, (0, 0, 255))
        if useJS:
            return jsRunGame(nw, maxtime, self.bts)
        else:
            return pyRunGame(nw, maxtime, self.bts)

    # Functions to compare noisy simulations to observations
    def runNoisyPath(self, toolname, position, maxtime = 20., useJS = False,
                     noise_position_static = 5., noise_position_moving = 5.,
                     noise_collision_direction = .2, noise_collision_elasticity = .2, noise_gravity = .1,
                     noise_object_friction = .1, noise_object_density = .1, noise_object_elasticity = .1):

        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]

        nw = noisifyWorld(self._world, noise_position_static, noise_position_moving,
                          noise_collision_direction, noise_collision_elasticity, noise_gravity,
                          noise_object_friction, noise_object_density, noise_object_elasticity)

        # Make sure the tool can be placed
        for tverts in tool:
            if nw.checkCollision(position, tverts):
                return None, None, -1

        placeTool = []
        for poly in tool:
            placeTool.append([(p[0] + position[0], p[1] + position[1]) for p in poly])

        nw.addPlacedCompound('PLACED', placeTool, (0, 0, 255))
        if useJS:
            return jsGetPath(nw, maxtime, self.bts)
        else:
            return pyGetPath(nw, maxtime, self.bts)

    def getToolNames(self):
        return self._tools.keys()

    def getWorldDims(self):
        return self._world.dims

    def exposeWorld(self):
        return self._world

    toolNames = property(getToolNames)
    worldDims = property(getWorldDims)
    world = property(exposeWorld)


def loadToolPicker(jsonfile, basicTimestep = 0.1):
    with open(jsonfile, 'rU') as jfl:
        return ToolPicker(json.load(jfl), basicTimestep)
