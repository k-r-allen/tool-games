from __future__ import division, print_function
import execjs
import json
import os
import pdb
from .js_contexts import modulepath, base_context, collision_context, context
from .helpers import filterCollisionEvents, stripGoal, updateObjects, NpEncoder
from .world import loadFromDict
from .viewer import *
import pygame as pg
import numpy as np
import warnings

__all__ = ['ToolPicker', 'loadToolPicker', 'JSRunner']

'''A class that encapsulates a Javascript context to run world through the JS kernel
Note: all run_* functions take the following arguments:
    worlddict [dict]: the dictionary representing the world object
    maxtime [float]: the time to run the world for before giving up
    timestep [float]: the time between returning positions/etc. (defaults to 0.1)
    noise_dict [dict]: a dictionary with the noise parameters to apply to the
        world. Defaults to the empty dict (no noise)
    return_world_dict [bool]: should the function also return a dictionary after
        adding noise to the world? Defaults to False
'''
class JSRunner(object):
    def __init__(self):
        ctxstr = (base_context.format(modulepath))
        self._ctx = execjs.compile(ctxstr)

    '''Runs the world forwards and returns a list with:
        0: A bool representing whether the goal condition was met
        1: A float representing the world time at the end
        2 (optional): A new dictionary with the noisified world
    '''
    def run_gw(self, worlddict, maxtime, timestep=0.1, noise_dict={},
               return_world_dict=False):
        return self._ctx.call('runGW', worlddict, maxtime, timestep,
                              noise_dict, return_world_dict)

    '''Runs the world for a single step and returns the world after that step
    '''
    def step_gw(self, worlddict, timestep=0.1):
        warnings.warn("Not complete -- works but mismatched to continuous run")
        return self._ctx.call('stepGW', worlddict, timestep)


    '''Runs the world forwards and returns a list with:
        0: A dict with each moveable object, including a list of its position
            at each timestep
        1: A bool representing whether the goal condition was met
        2: A float representing the world time at the end
        3 (optional): A new dictionary with the noisified world
    '''
    def run_gw_path(self, worlddict, maxtime, timestep=0.1, noise_dict={},
                    return_world_dict=False):
        return self._ctx.call('getGWPath', worlddict, maxtime, timestep,
                              noise_dict, return_world_dict)

    '''Runs the world forwards and returns a list with:
        0: A dict with each moveable object, including two lists of its position
            and rotation at each timestep
        1: A bool representing whether the goal condition was met
        2: A float representing the world time at the end
        3 (optional): A new dictionary with the noisified world
    '''
    def run_gw_path_and_rot(self, worlddict, maxtime, timestep=0.1,
                            noise_dict={}, return_world_dict=False):
        return self._ctx.call('getGWPathAndRot', worlddict, maxtime, timestep,
                              noise_dict, return_world_dict)

    '''Runs the world forwards and returns a list with:
        0: A dict with each moveable object, including a lists consisting of
            lists for each time point representing [pos_x, pos_y, rotation,
            vel_x, vel_y]
        1: A bool representing whether the goal condition was met
        2: A float representing the world time at the end
        3 (optional): A new dictionary with the noisified world
    '''
    def run_gw_state_path(self, worlddict, maxtime, timestep=0.1,
                            noise_dict={}, return_world_dict=False):
        return self._ctx.call('getGWStatePath', worlddict, maxtime, timestep,
                              noise_dict, return_world_dict)


    '''Runs the world forwards and returns geometries of dynamic objects:
        0: A dict with each moveable object, including a list of:
            a: the object type
            b: the object geometry (Poly: vertices, Ball: [pos, rad], Compound: list of poly vertices)
            c: the object velocity
        1: A bool representing whether the goal condition was met
        2: A float representing the world time at the end
        3 (optional): A new dictionary with the noisified world
    '''
    def run_gw_geom_path(self, worlddict, maxtime, timestep=0.1,
                            noise_dict={}, return_world_dict=False):
        return self._ctx.call('getGWGeomPath', worlddict, maxtime, timestep,
                              noise_dict, return_world_dict)

    '''Runs the world forwards and returns a list with:
        0: A dict with each moveable object, including a list of its position
            at each timestep
        1: A list of collisions, with each collision comprised of [object
            1 name, object 2 name, begin time, end time]
        2: A bool representing whether the goal condition was met
        3: A float representing the world time at the end
        4 (optional): A new dictionary with the noisified world
    Note:
        Also takes in the collision_slop argument (default=0.2001) which is
        used to ignore collision disconnects less than that length (due to
        physics engine jitters)
    '''
    def run_gw_collision_path(self, worlddict, maxtime, timestep=0.1,
                            noise_dict={}, return_world_dict=False, objAdjust=None,
                            collision_slop=0.2001):

        fnc = 'getGWCollisionPathAndRot'
        if objAdjust:
            worlddict = updateObjects(worlddict, objAdjust)
        if return_world_dict:
            path, col, end, t, w = self._ctx.call('getGWCollisionPathAndRot',
                                                  worlddict, maxtime, timestep,
                                                  noise_dict, True)
        else:
            path, col, end, t = self._ctx.call(fnc,
                                               worlddict, maxtime, timestep,
                                               noise_dict, False)
        fcol = filterCollisionEvents(col, collision_slop)
        r = [path, fcol, end, t]
        if return_world_dict:
            r.append(w)
        return r

    def run_gw_collision_bump_path(self, worldDict, maxtime, bumpTime, bumpObj, bumpImpulse, bumpLocation=None, timeStep=0.1,
                                    noiseDict={}, return_world_dict=False,objAdjust=None):
        if objAdjust:
            worldDict = updateObjects(worldDict, objAdjust)
        if all([v == 0 for v in noiseDict.values()]):
            noiseDict = {}

        if bumpLocation is not None:
            return self._ctx.call('getGWPathBumpAndNoiseLocation',
                worldDict, bumpTime, bumpObj, bumpImpulse, bumpLocation, maxtime, timeStep, noiseDict, return_world_dict)
        else:
            return self._ctx.call('getGWPathBumpAndNoise',
                    worldDict, bumpTime, bumpObj, bumpImpulse, maxtime, timeStep, noiseDict, return_world_dict)

'''Takes in a worlddict and creates a world that can quickly check whether
vertices placed in that world would cause a collision
Args for the function:
    vertices_list: a list of convex hulls (lists of vertices) to place. This
        should be relative to the (0, 0) point
    position: the position to place those vertices around
'''
class CollisionChecker(object):
    def __init__(self, worlddict):
        ctxstr = (context.format(modulepath, json.dumps(worlddict, cls=NpEncoder)))
        self._ctx = execjs.compile(ctxstr)

    def __call__(self, vertices_list, position):
        for vl in vertices_list:
            if self._ctx.call('checkSinglePlaceCollide', vl, position):
                return True
        return False


class ToolPicker(object):

    def __init__(self, gamedict, basicTimestep=0.1, worldTimestep=0.01, maxTime=20., checkThruPy=True, tnm=None):
        self._worlddict = gamedict['world']
        self._worlddict['bts'] = worldTimestep
        self._worlddict = json.loads(json.dumps(self._worlddict, cls=NpEncoder))
        self._wdng = stripGoal(self._worlddict)
        self.bts = basicTimestep
        self.maxTime = maxTime
        self.wts = worldTimestep
        if tnm is not None:
            self._tnm = tnm
        self._tools = gamedict['tools']
        self._toolNames = list(self._tools.keys())
        self.t = 0
        ctxstr = (context.format(modulepath, json.dumps(self._worlddict, cls=NpEncoder)))
        self._ctx = execjs.compile(ctxstr)
        self._pycheck = checkThruPy
        if checkThruPy:
            self._pyworld = loadFromDict(self._worlddict)

    def _reset_pyworld(self):
        self._pyworld = loadFromDict(self._worlddict)

    def _get_image_array(self, worlddict, path, sample_ratio=1):
        if path is None:
            imgs = makeImageArrayNoPath(worlddict, self.maxTime/self.bts/sample_ratio)
        else:
            imgs = makeImageArray(worlddict, path, sample_ratio)
        imgdata = np.array([pg.surfarray.array3d(img).swapaxes(0,1) for img in imgs])
        return imgdata

    def drawPathSingleImage(self, wd, path, with_tools=False):
        if path is None:
            world = loadFromDict(wd)
            sc = drawWorld(world, backgroundOnly=False)
            img = sc
        else:
            img = drawPathSingleImage(wd, path)

        imgdata = pg.surfarray.array3d(img).swapaxes(0,1)
        return imgdata

    def drawTool(self, tool):
        tool_to_draw = self._tools[self._toolNames[tool]]
        img = drawTool(tool_to_draw, color=(0,0,255), toolbox_size=(90, 90))
        return img

    def checkPlacementCollide(self, toolname, position):
        #for tverts in self._tools[toolname]:
        #    if self._ctx.call('checkSinglePlaceCollide', tverts, position):
        #        return True
        #return False
        if any(np.array(position) <= 0.0) or any(np.array(position)>=600.0):
            return True
        if self._pycheck:
            for tverts in self._tools[toolname]:
                if self._pyworld.checkCollision(position, tverts):
                    return True
            return False
        else:
            return self._ctx.call('checkMultiPlaceCollide', self._tools[toolname], position)

    def runPlacement(self, toolname, position, maxtime=20., returnDict=False,
                     stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('runGWPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, {}, returnDict)

    def observePlacementPath(self, toolname, position, maxtime=20., returnDict=False,
                             stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWPathPlacement', wd,
                              self._tools[toolname], position, maxtime,
                              self.bts, {}, returnDict)

    def observePath(self, maxtime=20., returnDict=False, stopOnGoal=True,
                    objAdjust=None):
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWStatePath', wd, maxtime, self.bts,
                              {}, returnDict)

    def observeFullPlacementPath(self, toolname, position, maxtime=20.,
                                 returnDict=False, stopOnGoal=True,
                                 objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1, None
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWPathAndRotPlacement', wd,
                              self._tools[toolname], position, maxtime,
                              self.bts, {}, returnDict)

    def observeGeomPath(self, toolname, position, maxtime=20.,
                        returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1, None
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWGeomPathPlacement', wd,
                              self._tools[toolname], position, maxtime,
                              self.bts, {}, returnDict)

    def observePlacementStatePath(self, toolname, position, returnDict=False,
                                  stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            if returnDict:
                return None, None, -1, None
            else:
                return None, None, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWStatePathPlacement', wd,
                              self._tools[toolname], position, self.maxTime,
                              self.bts, {}, returnDict)

    def observeCollisionEvents(self, toolname, position, maxtime=20.,
                               collisionSlop=.2001, returnDict=False,
                               stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        if returnDict:
            path, col, end, t, w = self._ctx.call('getGWCollisionPathPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, {},True)
        else:
            path, col, end, t = self._ctx.call('getGWCollisionPathPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, {}, False)
        fcol = filterCollisionEvents(col, collisionSlop)
        r = [path, fcol, end, t]
        if returnDict:
            r.append(w)
        return r

    def observeFullCollisionEvents(self, toolname, position, maxtime=20.,
                               collisionSlop=.2001, returnDict=False,
                               stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            return None, None, -1, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        if returnDict:
            path, col, end, t, w = self._ctx.call('getGWCollisionPathAndRotPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, {},True)
        else:
            path, col, end, t = self._ctx.call('getGWCollisionPathAndRotPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, {}, False)
        fcol = filterCollisionEvents(col, collisionSlop)
        r = [path, fcol, end, t]
        if returnDict:
            r.append(w)
        return r

    def placeObject(self, toolname, position):
        raise NotImplementedError(
            'Direct placement not allowed in new ToolPicker')

    def noisifySelf(self, noise_position_static=5., noise_position_moving=5.,
                    noise_collision_direction=.2, noise_collision_elasticity=.2, noise_gravity=.1,
                    noise_object_friction=.1, noise_object_density=.1, noise_object_elasticity=.1):
        raise NotImplementedError(
            'Direct noisification not allowed in new ToolPicker -- use runNoisyPlacement()')

    def runNoisyPlacement(self, toolname, position, maxtime=20.,
                          noise_position_static=0, noise_position_moving=0,
                          noise_collision_direction=0, noise_collision_elasticity=0, noise_gravity=0,
                          noise_object_friction=0, noise_object_density=0, noise_object_elasticity=0,
                          returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        #if noise_object_friction > 0 or noise_object_density > 0 or noise_object_elasticity > 0:
        #    warnings.warn("Noise on objects not yet implemented -- will have no effect")
        ndict = {
            'noise_position_static': noise_position_static,
            'noise_position_moving': noise_position_moving,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('runGWPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, ndict, returnDict)

    def observeNoisyPlacementStatePath(self, toolname, position, ndict={},
                                       returnDict=False, stopOnGoal=True,
                                       objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        # Make sure the tool can be placed
        if self.checkPlacementCollide(toolname, position):
            if returnDict:
                return None, None, -1, None
            else:
                return None, None, -1
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWStatePathPlacement', wd,
                              self._tools[toolname], position, self.maxTime,
                              self.bts, ndict, returnDict)

    def runNoisyPath(self, toolname, position, maxtime=20.,
                     noise_position_static=0, noise_position_moving=0,
                     noise_collision_direction=0, noise_collision_elasticity=0, noise_gravity=0,
                     noise_object_friction=0, noise_object_density=0, noise_object_elasticity=0,
                     returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        #if noise_object_friction > 0 or noise_object_density > 0 or noise_object_elasticity > 0:
        #    warnings.warn("Noise on objects not yet implemented -- will have no effect")
        ndict = {
            'noise_position_static': noise_position_static,
            'noise_position_moving': noise_position_moving,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWPathPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, ndict, returnDict)

    def runFullNoisyPath(self, toolname, position, maxtime=20.,
                     noise_position_static=0, noise_position_moving=0,
                     noise_collision_direction=0, noise_collision_elasticity=0, noise_gravity=0,
                     noise_object_friction=0, noise_object_density=0, noise_object_elasticity=0,
                     returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        #if noise_object_friction > 0 or noise_object_density > 0 or noise_object_elasticity > 0:
        #    warnings.warn("Noise on objects not yet implemented -- will have no effect")
        ndict = {
            'noise_position_static': noise_position_static,
            'noise_position_moving': noise_position_moving,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        if all([v == 0 for v in ndict.values()]):
            ndict = {}
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWPathAndRotPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, ndict, returnDict)

    def runNoisyGeomPath(self, toolname, position, maxtime=20.,
                     noise_position_static=0, noise_position_moving=0,
                     noise_collision_direction=0, noise_collision_elasticity=0, noise_gravity=0,
                     noise_object_friction=0, noise_object_density=0, noise_object_elasticity=0,
                     returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        #if noise_object_friction > 0 or noise_object_density > 0 or noise_object_elasticity > 0:
        #    warnings.warn("Noise on objects not yet implemented -- will have no effect")
        ndict = {
            'noise_position_static': noise_position_static,
            'noise_position_moving': noise_position_moving,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        if all([v == 0 for v in ndict.values()]):
            ndict = {}
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWGeomPathPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, ndict, returnDict)

    def runFullNoisyPathDict(self, toolname, position, maxtime=20.,ndict={},
                     returnDict=False, stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        if ndict != {}:
            warnings.warn("Noise on objects not yet implemented -- will have no effect")
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        return self._ctx.call('getGWPathAndRotPlacement', wd, self._tools[toolname],
                              position, maxtime, self.bts, ndict, returnDict)

    def runNoisyBumpPath(self, toolname, position, bumptime, bumpname, bumpimpulse, bumpLocation=None,
                         maxtime=20., noise_position_static=0,
                         noise_position_moving=0, noise_collision_direction=0,
                         noise_collision_elasticity=0, noise_gravity=0,
                         noise_object_friction=0, noise_object_density=0,
                         noise_object_elasticity=0, returnDict=False,
                         stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        #if noise_object_friction > 0 or noise_object_density > 0 or noise_object_elasticity > 0:
        #    warnings.warn("Noise on objects not yet implemented -- will have no effect")
        ndict = {
            'noise_position_static': 0,
            'noise_position_moving': 0,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        # Skip noisification if no noisy parameters added
        if all([v == 0 for v in ndict.values()]):
            ndict = {}

        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)

        if bumpLocation is not None:
            return self._ctx.call('getGWPathBumpAndNoiseLocationPlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse, bumpLocation,
                              maxtime, self.bts, ndict, returnDict)
        else:
            return self._ctx.call('getGWPathBumpAndNoisePlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse,
                              maxtime, self.bts, ndict, returnDict)

    def runNoisyBumpPathDict(self, toolname, position, bumptime, bumpname, bumpimpulse, bumpLocation=None,
                         maxtime=20., ndict={}, returnDict=False,
                         stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        if ndict != {}:
            if ndict['noise_object_friction'] > 0 or ndict['noise_object_density'] > 0 or ndict['noise_object_elasticity'] > 0:
                warnings.warn("Noise on objects not yet implemented -- will have no effect")

        # Skip noisification if no noisy parameters added
        if all([v == 0 for v in ndict.values()]) or ndict == {}:
            ndict = {}

        else:
            ndict['noise_position_static'] = 0
            ndict['noise_position_moving'] = 0

        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)

        if bumpLocation is not None:
            return self._ctx.call('getGWPathBumpAndNoiseLocationPlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse, bumpLocation,
                              maxtime, self.bts, ndict, returnDict)
        else:
            return self._ctx.call('getGWPathBumpAndNoisePlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse,
                              maxtime, self.bts, ndict, returnDict)

    def runNoisyStartBumpPathDict(self, toolname, position, bumptime, bumpname, bumpimpulse, bumpLocation=None,
                         maxtime=20., ndict={}, returnDict=False, stopOnGoal=True,
                         objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        if ndict['noise_object_friction'] > 0 or ndict['noise_object_density'] > 0 or ndict['noise_object_elasticity'] > 0:
            warnings.warn("Noise on objects not yet implemented -- will have no effect")

        # Skip noisification if no noisy parameters added
        if all([v == 0 for v in ndict.values()]):
            ndict = {}

        else:
            ndict['noise_position_static'] = 0
            ndict['noise_position_moving'] = 0

        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng

        if objAdjust:
            wd = updateObjects(wd, objAdjust)

        if bumpLocation is not None:
            return self._ctx.call('getGWPathWithBumpLocationPlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse, bumpLocation,
                              maxtime, self.bts, ndict, returnDict)
        else:
            return self._ctx.call('getGWPathWithBumpPlacement', wd,
                              self._tools[toolname], position,
                              bumptime, bumpname, bumpimpulse,
                              maxtime, self.bts, ndict, returnDict)


    def observeNoisyFullCollisionEvents(self, toolname, position, maxtime=20.,
                                        noise_position_static=0,
                                        noise_position_moving=0, noise_collision_direction=0,
                                        noise_collision_elasticity=0, noise_gravity=0,
                                        noise_object_friction=0, noise_object_density=0,
                                        noise_object_elasticity=0,
                                        collisionSlop=.2001, returnDict=False,
                                        stopOnGoal=True, objAdjust=None):
        assert toolname in self._tools.keys(), "That tool does not exist!"
        tool = self._tools[toolname]
        ndict = {
            'noise_position_static': 0,
            'noise_position_moving': 0,
            'noise_collision_direction': noise_collision_direction,
            'noise_collision_elasticity': noise_collision_elasticity,
            'noise_gravity': noise_gravity,
            'noise_object_friction': noise_object_friction,
            'noise_object_density': noise_object_density,
            'noise_object_elasticity': noise_object_elasticity
        }
        # Skip noisification if no noisy parameters added
        if all([v == 0 for v in ndict.values()]):
            ndict = {}
        if stopOnGoal:
            wd = self._worlddict
        else:
            wd = self._wdng
        if objAdjust:
            wd = updateObjects(wd, objAdjust)
        if returnDict:
            path, col, end, t, w = self._ctx.call('getGWCollisionPathAndRotPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, ndict,True)
        else:
            path, col, end, t = self._ctx.call('getGWCollisionPathAndRotPlacement', wd,
                                               self._tools[toolname], position,
                                               maxtime, self.bts, ndict, False)
        #fcol = filterCollisionEvents(col, collisionSlop)
        r = [path, end, t]
        if returnDict:
            r.append(w)
        return r

    def getToolNames(self):
        return self._tools.keys()

    def getWorldDims(self):
        return self._worlddict['dims']

    def getObjects(self):
        #this should only be used for getting initial positions of objects!
        world = loadFromDict(self._worlddict)
        return world.objects

    def exposeWorld(self):
        warnings.warn(
            "Exposing world returns a python object -- may differ from JS used in ToolPicker")
        return loadFromDict(self._worlddict)

    def toolBB(self, toolname):
        assert toolname in self.toolNames, "Tool not found: " + str(toolname)
        tool = self._tools[toolname]
        minx = 99999999
        miny = 99999999
        maxx = -99999999
        maxy = -99999999
        for p in tool:
            for v in p:
                if v[0] < minx:
                    minx = v[0]
                if v[0] > maxx:
                    maxx = v[0]
                if v[1] < miny:
                    miny = v[1]
                if v[1] > maxy:
                    maxy = v[1]
        return [[minx, miny], [maxx, maxy]]

    toolNames = property(getToolNames)
    worldDims = property(getWorldDims)
    world = property(exposeWorld)
    objects = property(getObjects)


def loadToolPicker(jsonfile, basicTimestep=0.1):
    with open(jsonfile, 'rU') as jfl:
        return ToolPicker(json.load(jfl), basicTimestep)
