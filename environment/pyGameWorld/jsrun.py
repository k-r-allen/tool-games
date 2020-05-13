from execjs import get
from .world import loadFromDict
from .helpers import filterCollisionEvents
import copy
import os, json

__all__ = ["jsRunGame", "pyRunGame", "jsGetPath", "pyGetPath", "jsGetStatePath", "pyGetStatePath", "jsGetCollisions", "pyGetCollisions", "pyGetCollisionsAddForces"]

jsruntime = get('Node')
jscontext = jsruntime.compile('''
    module.paths.push('%s');
    var pg = require('PhysicsGaming');
    function runGW(worldDict, maxtime, stepSize) {
        var w = pg.loadFromDict(worldDict);
        var running = true;
        var t = 0;
        while (running) {
            w.step(stepSize);
            t += stepSize;
            if (w.checkEnd() || (t >= maxtime)) {
                running = false;
            }
        }
        return [w.checkEnd(), t];
    };
''' % os.path.join(os.path.dirname(__file__), 'node_modules'))

jscontext_path = jsruntime.compile('''
    module.paths.push('%s');
    var pg = require('PhysicsGaming');
    function getGWPath(worldDict, maxtime, stepSize) {
        var w = pg.loadFromDict(worldDict);
        var running = true;
        var t = 0;
        var pathdict = {};
        var tracknames = [];
        for (onm in w.objects) {
            var o = w.objects[onm];
            if (!o.isStatic()) {
                tracknames.push(onm);
                pathdict[onm] = [o.getPos()];
            }
        }
        while (running) {
            w.step(stepSize);
            t += stepSize;
            for (var i = 0; i < tracknames.length; i++) {
                onm = tracknames[i];
                pathdict[onm].push(w.objects[onm].getPos());
            }
            if (w.checkEnd() || (t >= maxtime)) {
                running = false;
            }
        }
        return [pathdict, w.checkEnd(), t];
    };
''' % os.path.join(os.path.dirname(__file__), 'node_modules'))

jscontext_statepath = jsruntime.compile('''
    module.paths.push('%s');
    var pg = require('PhysicsGaming');
    function getGWStatePath(worldDict, maxtime, stepSize) {
        var w = pg.loadFromDict(worldDict);
        var running = true;
        var t = 0;
        var pathdict = {};
        var tracknames = [];
        for (onm in w.objects) {
            var o = w.objects[onm];
            if (!o.isStatic()) {
                tracknames.push(onm);
                pathdict[onm] = [[o.getPos()[0], o.getPos()[1], o.getRot(), o.getVel()[0], o.getVel()[1]]];
            }
        }
        while (running) {
            w.step(stepSize);
            t += stepSize;
            for (var i = 0; i < tracknames.length; i++) {
                onm = tracknames[i];
                pathdict[onm].push([w.objects[onm].getPos()[0], w.objects[onm].getPos()[1], w.objects[onm].getRot(), w.objects[onm].getVel()[0], w.objects[onm].getVel()[1]]);
            }
            if (w.checkEnd() || (t >= maxtime)) {
                running = false;
            }
        }
        return [pathdict, w.checkEnd(), t];
    };
''' % os.path.join(os.path.dirname(__file__), 'node_modules'))

jscontext_collision = jsruntime.compile('''
    module.paths.push('%s');
    var pg = require('PhysicsGaming');
    function getGWPath(worldDict, maxtime, stepSize) {
        var w = pg.loadFromDict(worldDict);
        var running = true;
        var t = 0;
        var pathdict = {};
        var tracknames = [];
        for (onm in w.objects) {
            var o = w.objects[onm];
            if (!o.isStatic()) {
                tracknames.push(onm);
                pathdict[onm] = [o.getPos()];
            }
        }
        while (running) {
            w.step(stepSize);
            t += stepSize;
            for (var i = 0; i < tracknames.length; i++) {
                onm = tracknames[i];
                pathdict[onm].push(w.objects[onm].getPos());
            }
            if (w.checkEnd() || (t >= maxtime)) {
                running = false;
            }
        }
        collisions = w.getCollisionEvents();

        return [pathdict, collisions, w.checkEnd(), t];
    };
''' % os.path.join(os.path.dirname(__file__), 'node_modules'))


def pyRunGame(gameworld, maxtime = 20., stepSize=.1):
    running = True
    t = 0
    while running:
        gameworld.step(stepSize)
        t += stepSize
        if gameworld.checkEnd() or (t >= maxtime):
            running = False
    return gameworld.checkEnd(), t

def pyGetPath(gameworld, maxtime = 20., stepSize = .1):
    running = True
    t = 0
    pathdict = dict()
    tracknames = []
    for onm, o in gameworld.objects.items():
        if not o.isStatic():
            tracknames.append(onm)
            pathdict[onm] = [o.position]
    while running:
        gameworld.step(stepSize)
        t += stepSize
        for onm in tracknames:
            pathdict[onm].append(gameworld.objects[onm].position)
        if gameworld.checkEnd() or (t >= maxtime):
            running = False
    return pathdict, gameworld.checkEnd(), t

def pyGetStatePath(gameworld, maxtime = 20., stepSize = .1):
    running = True
    t = 0
    pathdict = dict()
    tracknames = []
    for onm, o in gameworld.objects.items():
        if not o.isStatic():
            tracknames.append(onm)
            pathdict[onm] = [[o.position, o.rotation, o.velocity]]
    while running:
        gameworld.step(stepSize)
        t += stepSize
        for onm in tracknames:
            pathdict[onm].append([gameworld.objects[onm].position[0], gameworld.objects[onm].position[1], gameworld.objects[onm].rotation, gameworld.objects[onm].velocity[0], gameworld.objects[onm].velocity[1]])
        if gameworld.checkEnd() or (t >= maxtime):
            running = False
    return pathdict, gameworld.checkEnd(), t

def pyGetCollisions(gameworld, maxtime = 20., stepSize = .1, collisionSlop = 0.2001):
    running = True
    t = 0
    pathdict = dict()
    tracknames = []
    for onm, o in gameworld.objects.items():
        if not o.isStatic():
            tracknames.append(onm)
            pathdict[onm] = [o.position]
    while running:
        gameworld.step(stepSize)
        t += stepSize
        for onm in tracknames:
            pathdict[onm].append(gameworld.objects[onm].position)
        if gameworld.checkEnd() or (t >= maxtime):
            running = False
    collisions = filterCollisionEvents(gameworld.collisionEvents, collisionSlop)
    return pathdict, collisions, gameworld.checkEnd(), t

def pyGetCollisionsAddForces(gameworld, force_times={}, maxtime = 20., stepSize = .1, collisionSlop = 0.2001):
    running = True
    t = 0
    pathdict = dict()
    tracknames = []
    for onm, o in gameworld.objects.items():
        if not o.isStatic():
            tracknames.append(onm)
            pathdict[onm] = [o.position]
    while running:
        gameworld.step(stepSize)
        t += stepSize
        if t in force_times.keys():
            for obj_force in force_times[t]:
                onm = obj_force[0]
                impulse = obj_force[1]
                position = obj_force[2]
                gameworld.objects[onm].kick(impulse, position)

        for onm in tracknames:
            pathdict[onm].append(gameworld.objects[onm].position)
        if gameworld.checkEnd() or (t >= maxtime):
            running = False
    collisions = filterCollisionEvents(gameworld.collisionEvents, collisionSlop)
    return pathdict, collisions, gameworld.checkEnd(), t

def jsRunGame(gameworld, maxtime = 20., stepSize=.1):
    w = gameworld.toDict()
    return jscontext.call('runGW', w, maxtime, stepSize)

def jsGetPath(gameworld, maxtime = 20., stepSize = .1):
    w = gameworld.toDict()
    return jscontext_path.call('getGWPath', w, maxtime, stepSize)

def jsGetStatePath(gameworld, maxtime = 20., stepSize = .1):
    w = gameworld.toDict()
    return jscontext_statepath.call('getGWStatePath', w, maxtime, stepSize)

def jsGetCollisions(gameworld, maxtime = 20., stepSize = .1, collisionSlop = 0.2001):
    w = gameworld.toDict()
    path,col,end,t = jscontext_collision.call('getGWPath', w, maxtime, stepSize)
    fcol = filterCollisionEvents(col, collisionSlop)
    return [path,fcol,end,t]
