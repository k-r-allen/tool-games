from __future__ import division, print_function
import pymunk as pm
import pygame as pg
import numpy as np
from scipy.stats import multivariate_normal as mvnm
from ..world import *
from ..constants import *
from ..object import *
from pygame.constants import *
#from .visualize_likelihoods import *
import pdb
__all__ = ['drawWorld', 'demonstrateWorld', 'demonstrateTPPlacement',
           'visualizePath', 'drawPathSingleImage', 'drawPathSingleImageWithTools', 'drawWorldWithTools', 'visualizeScreen', 'drawPathSingleImageBasic',
           'makeImageArray', 'makeImageArrayNoPath','drawTool', '_draw_line_gradient',
           'drawMultiPathSingleImage', 'drawMultiPathSingleImageBasic']

COLORS=[(255,0,255,255), (225,225,0, 255),(0, 255, 255, 255)]
WHITE = (255, 255, 255, 255)
def _lighten_rgb(rgba, amt=.2):
    assert 0 <= amt <= 1, "Lightening must be between 0 and 1"
    r = int(255- ((255-rgba[0]) * (1-amt)))
    g = int(255- ((255-rgba[1]) * (1-amt)))
    b = int(255- ((255-rgba[2]) * (1-amt)))
    if len(rgba) == 3:
        return (r, g, b)
    else:
        return (r, g, b, rgba[3])

def _draw_line_gradient(start, end, steps, rgba, surf):
    diffs = np.array(end) - np.array(start)
    dX = (end[0] - start[0]) / steps
    dY = (end[1] - start[1]) / steps

    points = np.array(start) + np.array([[dX,dY]])*np.array([range(0,steps),]*2).transpose()
    cols = [_lighten_rgb(rgba, amt=0.9*step/steps) for step in range(0, steps)]
    for i, point in enumerate(points[:-1]):
        pg.draw.line(surf, cols[i], point, points[i+1], 3)
    return surf

def _filter_unique(mylist):
    newlist = []
    for ml in mylist:
        if ml not in newlist:
            newlist.append(ml)
    return newlist

def _draw_obj(o, s, makept, lighten_amt=0):
    if o.type == 'Poly':
        vtxs = [makept(v) for v in o.vertices]
        col = _lighten_rgb(o.color, lighten_amt)
        pg.draw.polygon(s, col, vtxs)
    elif o.type == 'Ball':
        pos = makept(o.position)
        rad = int(o.radius)
        col = _lighten_rgb(o.color, lighten_amt)
        pg.draw.circle(s, col, pos, rad)
        # Draw small segment that adds a window
        rot = o.rotation
        mixcol = [int((3.*oc + 510.)/5.) for oc in o.color]
        mixcol = _lighten_rgb(mixcol, lighten_amt)
        for radj in range(5):
            ru = radj*np.pi / 2.5 + rot
            pts = [(.65*rad*np.sin(ru) + pos[0], .65*rad*np.cos(ru) + pos[1]),
                   (.7 * rad * np.sin(ru) + pos[0], .7 * rad * np.cos(ru) + pos[1]),
                   (.7 * rad * np.sin(ru+np.pi/20.) + pos[0], .7 * rad * np.cos(ru+np.pi/20.) + pos[1]),
                   (.65 * rad * np.sin(ru+np.pi/20.) + pos[0], .65 * rad * np.cos(ru+np.pi/20.) + pos[1])]
            pg.draw.polygon(s, mixcol, pts)
    elif o.type == 'Segment':
        pa, pb = [makept(p) for p in o.points]
        col = _lighten_rgb(o.color, lighten_amt)
        pg.draw.line(s, col, pa, pb, o.r)
    elif o.type == 'Container':
        for poly in o.polys:
            ocol = col = _lighten_rgb(o.outer_color, lighten_amt)
            vtxs = [makept(p) for p in poly]
            pg.draw.polygon(s, ocol, vtxs)
        garea = [makept(p) for p in o.vertices]
        if o.inner_color is not None:
            acolor = (o.inner_color[0], o.inner_color[1], o.inner_color[2], 128)
            acolor = _lighten_rgb(acolor, lighten_amt)
            pg.draw.polygon(s, acolor, garea)
    elif o.type == 'Compound':
        col = _lighten_rgb(o.color, lighten_amt)
        for poly in o.polys:
            vtxs = [makept(p) for p in poly]
            pg.draw.polygon(s, col, vtxs)
    elif o.type == 'Goal':
        if o.color is not None:
            col = _lighten_rgb(o.color, lighten_amt)
            vtxs = [makept(v) for v in o.vertices]
            pg.draw.polygon(s, col, vtxs)
    else:
        print ("Error: invalid object type for drawing:", o.type)

def _draw_tool(toolverts, makept, size=[90, 90], color=(0,0,0,255)):
    s = pg.Surface(size)
    s.fill(WHITE)
    for poly in toolverts:
        vtxs = [makept(p) for p in poly]
        pg.draw.polygon(s, color, vtxs)
    return s

def drawWorld(world, backgroundOnly=False, lightenPlaced=False):
    s = pg.Surface(world.dims)
    s.fill(world.bk_col)

    def makept(p):
        return [int(i) for i in world._invert(p)]

    for b in world.blockers.values():
        drawpts = [makept(p) for p in b.vertices]
        pg.draw.polygon(s, b.color, drawpts)

    for o in world.objects.values():
        if not backgroundOnly or o.isStatic():
            if lightenPlaced and o.name == 'PLACED':
                _draw_obj(o, s, makept, .5)
            else:
                _draw_obj(o, s, makept)
    return s

def drawTool(tool):

    def maketoolpt(p):
        return [int(p[0] + 45), int(45-p[1])]

    s = _draw_tool(tool, maketoolpt, [90,90])

    return s

def drawWorldWithTools(tp, backgroundOnly=False, worlddict=None):
    if worlddict is not None:
        world = loadFromDict(worlddict)
    else:
        world = loadFromDict(tp._worlddict)
    s = pg.Surface((world.dims[0] + 150, world.dims[1]))
    s.fill(world.bk_col)

    def makept(p):
        return [int(i) for i in world._invert(p)]

    def maketoolpt(p):
        return [int(p[0] + 45), int(45-p[1])]

    for b in world.blockers.values():
        drawpts = [makept(p) for p in b.vertices]
        pg.draw.polygon(s, b.color, drawpts)

    for o in world.objects.values():
        if not backgroundOnly or o.isStatic():
            _draw_obj(o, s, makept)

    for i, t in enumerate(tp._tools.keys()):
        col = COLORS[i]
        newsc = pg.Surface([96, 96])
        newsc.fill(col)
        toolsc = _draw_tool(tp._tools[t], maketoolpt, [90,90])
        newsc.blit(toolsc, [3, 3])
        s.blit(newsc, (630, 137 + 110*i))
    return s

def demonstrateWorld(world, hz = 30.):
    pg.init()
    sc = pg.display.set_mode(world.dims)
    clk = pg.time.Clock()
    sc.blit(drawWorld(world), (0,0))
    pg.display.flip()
    running = True
    tps = 1./hz
    clk.tick(hz)
    dispFinish = True
    while running:
        world.step(tps)
        sc.blit(drawWorld(world), (0, 0))
        pg.display.flip()
        clk.tick(hz)
        for e in pg.event.get():
            if e.type == QUIT:
                running = False
        if dispFinish and world.checkEnd():
            print("Goal accomplished")
            dispFinish = False
    pg.quit()

def demonstrateTPPlacement(toolpicker, toolname, position, maxtime=20.,
                           noise_dict=None, hz=30.):
    tps = 1./hz
    toolpicker.bts = tps
    if noise_dict:
        pth, ocm, etime, wd = toolpicker.runFullNoisyPath(toolname, position, maxtime, returnDict=True, **noise_dict)
    else:
        pth, ocm, etime, wd = toolpicker.observeFullPlacementPath(toolname, position, maxtime, returnDict=True)
    world = loadFromDict(wd)
    print (ocm)
    pg.init()
    sc = pg.display.set_mode(world.dims)
    clk = pg.time.Clock()
    sc.blit(drawWorld(world), (0, 0))
    pg.display.flip()
    clk.tick(hz)
    t = 0
    i = 0
    dispFinish = True
    while t < etime:
        for onm, o in world.objects.items():
            if not o.isStatic():
                o.setPos(pth[onm][0][i])
                o.setRot(pth[onm][1][i])
        i += 1
        t += tps
        sc.blit(drawWorld(world), (0,0))
        pg.display.flip()
        for e in pg.event.get():
            if e.type == QUIT:
                pg.quit()
                return
    pg.quit()

def visualizePath(worlddict, path, hz=30.):
    world = loadFromDict(worlddict)
    pg.init()
    sc = pg.display.set_mode(world.dims)
    clk = pg.time.Clock()
    sc.blit(drawWorld(world), (0, 0))
    pg.display.flip()
    clk.tick(hz)
    if len(path[(list(path.keys())[0])]) == 2:
        nsteps = len(path[list(path.keys())[0]][0])
    else:
        nsteps = len(path[list(path.keys())[0]])

    for i in range(nsteps):
        for onm, o in world.objects.items():
            if not o.isStatic():
                if len(path[onm])==2:
                    o.setPos(path[onm][0][i])
                    o.setRot(path[onm][1][i])
                else:
                    o.setPos(path[onm][i][0:2])
                    #o.setRot(path[onm][i][2])
        sc.blit(drawWorld(world), (0,0))
        pg.display.flip()
        for e in pg.event.get():
            if e.type == QUIT:
                pg.quit()
                return
        clk.tick(hz)
    pg.quit()

def makeImageArray(worlddict, path, sample_ratio=1):
    world = loadFromDict(worlddict)
    #pg.init()
    images = [drawWorld(world)]
    if len(path[(list(path.keys())[0])]) == 2:
        nsteps = len(path[list(path.keys())[0]][0])
    else:
        nsteps = len(path[list(path.keys())[0]])

    for i in range(1,nsteps,sample_ratio):
        for onm, o in world.objects.items():
            if not o.isStatic():
                if len(path[onm])==2:
                    o.setPos(path[onm][0][i])
                    o.setRot(path[onm][1][i])
                else:
                    o.setPos(path[onm][i][0:2])
                    o.setRot(path[onm][i][2])
        images.append(drawWorld(world))
    return images

def makeImageArrayNoPath(worlddict, path_length):
    world = loadFromDict(worlddict)
    #pg.init()
    images = [drawWorld(world)]
    nsteps = path_length
    return images*int(nsteps)

def visualizeScreen(tp):
    #pg.init()
    pg.display.set_mode((10,10))
    s = drawWorldWithTools(tp, backgroundOnly=False)
    i = s.convert_alpha()
    pg.image.save(i, 'test.png')
    pg.quit()

def drawPathSingleImageWithTools(tp, path, pathSize=3, lighten_amt=.5, worlddict=None, with_tools=False):
    # set up the drawing
    if worlddict is None:
        worlddict = tp._worlddict
    world = loadFromDict(worlddict)
    #pg.init()
    #sc = pg.display.set_mode(world.dims)
    if not with_tools:
        sc = drawWorld(world, backgroundOnly=True)#, worlddict=worlddict)
    else:
        sc = drawWorldWithTools(tp, backgroundOnly=True, worlddict=worlddict)
    def makept(p):
        return [int(i) for i in world._invert(p)]
    # draw the paths in the background
    for onm, o in world.objects.items():
        if not o.isStatic():
            if o.type == 'Container':
                col = o.outer_color
            else:
                col = o.color
            pthcol = _lighten_rgb(col, lighten_amt)
            if len(path[onm]) == 2:
                poss = path[onm][0]
            else:
                poss = [path[onm][i][0:2] for i in range(0, len(path[onm]))]
            #for p in poss:
            #    pg.draw.circle(sc, pthcol, makept(p), pathSize)
            pts = _filter_unique([makept(p) for p in poss])

            if len(pts) > 1:
                steps = len(pts)
                cols = [_lighten_rgb(col, amt=0.9*step/steps) for step in range(0, steps)]
                for i,pt in enumerate(pts[:-1]):
                    color = cols[i]
                    pg.draw.line(sc, color, pt, pts[i+1], 3)
                    #_draw_line_gradient(pt, pts[i+1], 5, col, sc)
                #pg.draw.lines(sc, pthcol, False, pts, pathSize)
    # Draw the initial tools, lightened
    for onm, o in world.objects.items():
        if not o.isStatic():
            _draw_obj(o, sc, makept, lighten_amt=lighten_amt)
    # Draw the end tools
    for onm, o in world.objects.items():
        if not o.isStatic():
            if len(path[onm])==2:
                o.setPos(path[onm][0][-1])
                o.setRot(path[onm][1][-1])
            else:
                o.setPos(path[onm][-1][0:2])
            _draw_obj(o, sc, makept)

    return sc

def drawPathSingleImage(worlddict, path, pathSize=3, lighten_amt=.5):
    # set up the drawing
    world = loadFromDict(worlddict)
    sc = drawWorld(world, backgroundOnly=True)
    def makept(p):
        return [int(i) for i in world._invert(p)]
    # draw the paths in the background
    for onm, o in world.objects.items():
        if not o.isStatic():
            if o.type == 'Container':
                col = o.outer_color
            else:
                col = o.color
            pthcol = _lighten_rgb(col, lighten_amt)
            if len(path[onm]) == 2:
                poss = path[onm][0]
            else:
                poss = [path[onm][i][0:2] for i in range(0, len(path[onm]))]
            #for p in poss:
            #    pg.draw.circle(sc, pthcol, makept(p), pathSize)
            pts = _filter_unique([makept(p) for p in poss])
            if len(pts) > 1:
                pg.draw.lines(sc, pthcol, False, pts, pathSize)
    # Draw the initial tools, lightened
    for onm, o in world.objects.items():
        if not o.isStatic():
            _draw_obj(o, sc, makept, lighten_amt=lighten_amt)
    # Draw the end tools
    for onm, o in world.objects.items():
        if not o.isStatic():
            if len(path[onm])==2:
                o.setPos(path[onm][0][-1])
                o.setRot(path[onm][1][-1])
            else:
                o.setPos(path[onm][-1][0:2])
            _draw_obj(o, sc, makept)

    return sc


def drawMultiPathSingleImage(worlddict, path_set, pathSize=3, lighten_amt=.5):
    # set up the drawing
    world = loadFromDict(worlddict)

    sc = drawWorld(world, backgroundOnly=True)
    def makept(p):
        return [int(i) for i in world._invert(p)]
    # draw the paths in the background
    for path in path_set:
        for onm, o in world.objects.items():
            if not o.isStatic():
                if o.type == 'Container':
                    col = o.outer_color
                else:
                    col = o.color
                pthcol = _lighten_rgb(col, lighten_amt)
                if len(path[onm]) == 2:
                    poss = path[onm][0]
                else:
                    poss = [path[onm][i][0:2] for i in range(0, len(path[onm]))]

                pts = _filter_unique([makept(p) for p in poss])
                if len(pts) > 1:
                    pg.draw.lines(sc, pthcol, False, pts, pathSize)
    # Draw the initial tools, lightened
    for onm, o in world.objects.items():
        if not o.isStatic():
            _draw_obj(o, sc, makept, lighten_amt=lighten_amt)
    # Draw the end tools
    for path in path_set:
        for onm, o in world.objects.items():
            if not o.isStatic():
                if len(path[onm])==2:
                    o.setPos(path[onm][0][-1])
                    o.setRot(path[onm][1][-1])
                else:
                    o.setPos(path[onm][-1][0:2])
                _draw_obj(o, sc, makept)

    return sc

def drawPathSingleImageBasic(sc, world, path, pathSize=3, lighten_amt=.5):
    # set up the drawing
    def makept(p):
        return [int(i) for i in world._invert(p)]
    # draw the paths in the background
    for onm, o in world.objects.items():
        if not o.isStatic():
            if o.type == 'Container':
                col = o.outer_color
            else:
                col = o.color
            pthcol = _lighten_rgb(col, lighten_amt)
            if len(path[onm]) == 2:
                poss = path[onm][0]
            else:
                poss = path[onm]
            #for p in poss:
            #    pg.draw.circle(sc, pthcol, makept(p), pathSize)
            pts = _filter_unique([makept(p) for p in poss])
            if len(pts) > 1:
                pg.draw.lines(sc, pthcol, False, pts, pathSize)
    # Draw the initial tools, lightened
    for onm, o in world.objects.items():
        if not o.isStatic():
            _draw_obj(o, sc, makept, lighten_amt=lighten_amt)
    # Draw the end tools
    for onm, o in world.objects.items():
        if not o.isStatic():
            if len(path[onm])==2:
                o.setPos(path[onm][0][-1])
                o.setRot(path[onm][1][-1])
            else:
                o.setPos(path[onm][-1])
            _draw_obj(o, sc, makept)
    return sc


def drawMultiPathSingleImageBasic(sc, world, path_set, pathSize=3, lighten_amt=.5):
    # set up the drawing
    def makept(p):
        return [int(i) for i in world._invert(p)]
    # draw the paths in the background
    for path in path_set:
        for onm, o in world.objects.items():
            if not o.isStatic():
                if o.type == 'Container':
                    col = o.outer_color
                else:
                    col = o.color
                pthcol = _lighten_rgb(col, lighten_amt)
                if len(path[onm]) == 2:
                    poss = path[onm][0]
                else:
                    poss = path[onm]
                #for p in poss:
                #    pg.draw.circle(sc, pthcol, makept(p), pathSize)
                pts = _filter_unique([makept(p) for p in poss])
                if len(pts) > 1:
                    pg.draw.lines(sc, pthcol, False, pts, pathSize)
    # Draw the initial tools, lightened
    for onm, o in world.objects.items():
        if not o.isStatic():
            _draw_obj(o, sc, makept, lighten_amt=lighten_amt)
    # Draw the end tools
    for path in path_set:
        for onm, o in world.objects.items():
            if not o.isStatic():
                if len(path[onm]) == 2:
                    o.setPos(path[onm][0][-1])
                    o.setRot(path[onm][1][-1])
                else:
                    o.setPos(path[onm][-1])
                _draw_obj(o, sc, makept)
    return sc

def drawTool(tool, color=(0,0,255), toolbox_size=(90, 90)):
    s = pg.Surface(toolbox_size)
    def resc(p):
        return [int(p[0] +toolbox_size[0]/2),
                int(toolbox_size[1]/2 - p[1])]
    s.fill((255,255,255))
    for poly in tool:
        pg.draw.polygon(s, color, [resc(p) for p in poly])

    s_arr = pg.surfarray.array3d(s)
    return s_arr

def _def_inv(p):
    return(p)

