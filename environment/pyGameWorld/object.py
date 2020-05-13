import pymunk as pm
import numpy as np
from .constants import * # ADD PERIOD HERE
from .helpers import *
import pdb
import copy
__all__ = ['PGPoly','PGBall','PGSeg','PGContainer','PGCompound','PGGoal','PGBlocker']

class PGObject(object):

    def __init__(self, name, otype, space, color, density, friction, elasticity):
        assert otype in ['Ball','Poly','Segment','Container', 'Compound','Goal','Blocker'], \
            "Illegal 'type' of object"
        self.name = name
        self.type = otype
        self.space = space
        self.color = color
        self.density = density
        self._cpBody = None
        self._cpShape = None

    def isStatic(self):
        return self._cpBody is None

    def getPos(self):
        assert not self.isStatic(), "Static bodies do not have a position"
        p = self._cpBody.position
        return np.array([p.x, p.y])

    def setPos(self, p):
        assert not self.isStatic(), "Static bodies do not have a position"
        assert len(p) == 2, "Setting position requires vector of length 2"
        self._cpBody.position = p

    def getVel(self):
        assert not self.isStatic(), "Static bodies do not have a velocity"
        v = self._cpBody.velocity
        return np.array([v.x, v.y])

    def setVel(self, v):
        assert not self.isStatic(), "Static bodies do not have a velocity"
        assert len(v) == 2, "Setting position requires vector of length 2"
        self._cpBody.velocity = v

    def getRot(self):
        assert not self.isStatic(), "Static bodies do not have a rotation"
        return self._cpBody.angle

    def setRot(self, a):
        assert not self.isStatic(), "Static bodies do not have a rotation"
        self._cpBody.angle = a

    def getMass(self):
        if self.isStatic():
            return 0
        else:
            return self._cpBody.mass

    def _exposeShapes(self):
        return [self._cpShape]

    def checkContact(self, object):
        for myshapes in self._exposeShapes():
            for oshapes in object._exposeShapes():
                if len(myshapes.shapes_collide(oshapes).points) > 0:
                    return True
        return False

    def setMass(self, val):
        assert val > 0, "Must set a positive mass value"
        if self.isStatic():
            raise Exception("Cannot set the mass of a static object")
        else:
            self._cpBody.mass = val

    def getFriction(self):
        assert self._cpShape is not None, "Shape not yet set"
        return self._cpShape.friction

    def setFriction(self, val):
        assert self._cpShape is not None, "Shape not yet set"
        assert val >= 0, "Friction must be greater than or equal to 0"
        self._cpShape.friction = val

    def getElasticity(self):
        assert self._cpShape is not None, "Shape not yet set"
        return self._cpShape.elasticity

    def setElasticity(self, val):
        assert self._cpShape is not None, "Shape not yet set"
        assert val >= 0, "Elasticity must be greater than or equal to 0"
        self._cpShape.elasticity = val

    def toGeom(self):
        if (self.type == "Poly"):
            return self.getVertices()
        elif (self.type == "Ball"):
            return [self.getPos(), self.getRadius()]
        elif self.type == "Container" or self.type == "Compound":
            return self.getPolys()
        else:
            print('not a valid object type')
            return None

    def kick(self, impulse, position, unsafe = False):
        assert not self.isStatic(), "Cannot kick a static object"
        if not unsafe:
            for s in self._exposeShapes():
                if not s.point_query(position):
                    raise AssertionError("Must kick an object within the object (or set as unsafe)")
        self._cpBody.apply_impulse_at_world_point(impulse, position)

    def distanceFromPoint(self, point):
        d, _ = self._cpShape.point_query(point)
        return d

    # Add pythonic decorators
    position = property(getPos, setPos)
    velocity = property(getVel, setVel)
    rotation = property(getRot, setRot)
    mass = property(getMass, setMass)
    friction = property(getFriction, setFriction)
    elasticity = property(getElasticity, setElasticity)

class PGPoly(PGObject):

    def __init__(self,name,space,vertices,density = DEFAULT_DENSITY,elasticity=DEFAULT_ELASTICITY,
                 friction=DEFAULT_FRICTION,color=DEFAULT_COLOR):
        PGObject.__init__(self, name, "Poly", space, color, density, friction, elasticity)

        #vertices = map(lambda v: map(float, v), vertices)
        vertices = [[float(vp) for vp in v] for v in vertices]
        loc = centroidForPoly(vertices)
        area = areaForPoly(vertices)
        mass = density * area

        if mass == 0:
            self._cpShape = pm.Poly(space.static_body, vertices)
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            space.add(self._cpShape)
        else:
            recenterPoly(vertices)
            imom = pm.moment_for_poly(mass, vertices)
            self._cpBody = pm.Body(mass, imom)
            self._cpShape = pm.Poly(self._cpBody, vertices)
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            self._cpBody.position = loc
            space.add(self._cpBody, self._cpShape)

    def getVertices(self):
        if self.isStatic():
            verts = [np.array(v) for v in self._cpShape.get_vertices()]
            verts.reverse()
        else:
            verts = []
            pos = self.position
            rot = self.rotation
            for v in self._cpShape.get_vertices():
                vcp = v.rotated(rot) + pos
                verts = [np.array(vcp)] + verts
                #verts.append(np.array(vcp))
        return verts

    def getArea(self):
        return areaForPoly(self.getVertices)

    # Overwrites for static polygons too
    def getPos(self):
        if self.isStatic():
            vertices = [[float(vp) for vp in v] for v in self.vertices]
            return centroidForPoly(vertices)
        else:
            return np.array(self._cpBody.position)

    vertices = property(getVertices)
    area = property(getArea)


class PGBall(PGObject):

    def __init__(self, name, space, position, radius, density = DEFAULT_DENSITY,
                 elasticity=DEFAULT_ELASTICITY, friction=DEFAULT_FRICTION,color=DEFAULT_COLOR):
        PGObject.__init__(self, name, "Ball", space, color, density, friction, elasticity)
        area = np.pi * radius * radius
        mass = density * area
        imom = pm.moment_for_circle(mass, 0, radius)
        if mass == 0:
            self._cpShape = pm.Circle(space.static_body, radius, position)
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            space.add(self._cpShape)
        else:
            self._cpBody = pm.Body(mass, imom)
            self._cpShape = pm.Circle(self._cpBody, radius, (0,0))
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            self._cpBody.position = position
            space.add(self._cpBody, self._cpShape)

    def getRadius(self):
        return self._cpShape.radius

    def getArea(self):
        r = self.getRadius()
        return np.pi * r * r

    # Overwrites for static circles too
    def getPos(self):
        if self.isStatic():
            return self._cpShape.offset
        else:
            return self._cpBody.position

    radius = property(getRadius)
    area = property(getArea)


class PGSeg(PGObject):

    def __init__(self, name, space, p1, p2, width, density = DEFAULT_DENSITY,
                 elasticity=DEFAULT_ELASTICITY, friction=DEFAULT_FRICTION,color=DEFAULT_COLOR):
        PGObject.__init__(self, name, "Segment", space, color, density, friction, elasticity)
        self.r = width / 2
        area = areaForSegment(p1, p2, self.r)
        mass = density*area
        if mass == 0:
            self._cpShape = pm.Segment(space.static_body, p1, p2, self.r)
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            space.add(self._cpShape)
        else:
            pos = pm.Vec2d((p1[0] + p2[0]) / 2., (p1[1] + p2[1]) / 2.)
            v1 = pm.Vec2d(p1) - pos
            v2 = pm.Vec2d(p2) - pos
            imom = pm.moment_for_segment(mass, v1, v2, 0)
            self._cpBody = pm.Body(mass, imom)
            self._cpShape = pm.Segment(self._cpBody, v1, v2, self.r)
            self._cpShape.elasticity = elasticity
            self._cpShape.friction = friction
            self._cpShape.collision_type = COLTYPE_SOLID
            self._cpShape.name = name
            self._cpBody.position = pos
            space.add(self._cpBody, self._cpShape)

    def getPoints(self):
        v1 = self._cpShape.a
        v2 = self._cpShape.b
        if self.isStatic():
            p1 = np.array(v1)
            p2 = np.array(v2)
        else:
            pos = self.getPos()
            rot = self.getRot()
            p1 = np.array(pos + v1.rotated(rot))
            p2 = np.array(pos + v2.rotated(rot))
        return p1,p2

    points = property(getPoints)


class PGContainer(PGObject):

    def __init__(self,name, space, ptlist, width, density = DEFAULT_DENSITY,
                 elasticity=DEFAULT_ELASTICITY, friction=DEFAULT_FRICTION,
                 inner_color=DEFAULT_GOAL_COLOR, outer_color=DEFAULT_COLOR):
        PGObject.__init__(self, name, "Container", space, outer_color, density, friction, elasticity)
        self.inner_color = inner_color
        self.outer_color = outer_color
        self.r = width / 2

        loc = centroidForPoly(ptlist)
        self.pos = np.array([loc.x, loc.y])
        ptlist = copy.deepcopy(ptlist)
        if density != 0:
            ptlist = recenterPoly(ptlist)
        #self.seglist = map(lambda p: pm.Vec2d(p), ptlist)
        self.seglist = [pm.Vec2d(p) for p in ptlist]

        self._area = np.pi * self.r * self.r
        imom = 0
        for i in range(len(self.seglist)-1):
            v1 = self.seglist[i]
            v2 = self.seglist[i+1]
            larea = 2*self.r* v1.get_distance(v2)
            self._area += larea
            imom += pm.moment_for_segment(larea*density, v1, v2, 0)

        mass = density * self._area
        if mass == 0:
            uBody = space.static_body
        else:
            self._cpBody = uBody = pm.Body(mass, imom)
            space.add(self._cpBody)

        self._cpPolyShapes = []
        self.polylist = segs2Poly(ptlist, self.r)

        for pl in self.polylist:
            pshp = pm.Poly(uBody, pl)
            pshp.elasticity = elasticity
            pshp.friction = friction
            pshp.collision_type = COLTYPE_SOLID
            pshp.name = name
            self._cpPolyShapes.append(pshp)
            space.add(pshp)

        # Make sure we have ccw
        if not polyValidate(ptlist):
            ptlist.reverse()

        self._cpSensor = pm.Poly(uBody, ptlist)
        self._cpSensor.sensor = True
        self._cpSensor.collision_type = COLTYPE_SENSOR
        self._cpSensor.name = name
        space.add(self._cpSensor)
        if mass != 0:
            self._cpBody.position = loc


    def getPolys(self):
        if self.isStatic():
            polys = self.polylist
        else:
            pos = self.position
            rot = self.rotation
            polys = []
            for i in range(len(self.polylist)):
                tpol = []
                for j in range(len(self.polylist[i])):
                    vj = pm.Vec2d(self.polylist[i][j])
                    tpol.append(np.array(pos + vj.rotated(rot)))
                polys.append(tpol)
        return polys

    def getPos(self):
        if self.isStatic():
            return self.pos
        else:
            p = self._cpBody.position
            return np.array([p.x, p.y])

    def getVertices(self):
        if self.isStatic():
            #return map(lambda s: np.array(s), self.seglist)
            return [np.array(s) for s in self.seglist]
        else:
            b = self._cpBody
            return [np.array(b.local_to_world(s)) for s in self.seglist]

    def pointIn(self, p):
        v = pm.Vec2d(p[0], p[1])
        return self._cpSensor.point_query(v)

    def getFriction(self):
        return self._cpPolyShapes[0].friction

    def setFriction(self, val):
        assert val >= 0, "Friction must be greater than or equal to 0"
        for s in self._cpPolyShapes:
            s.friction = val

    def getElasticity(self):
        return self._cpPolyShapes[0].elasticity

    def setElasticity(self, val):
        assert val >= 0, "Elasticity must be greater than or equal to 0"
        for s in self._cpPolyShapes:
            s.elasticity = val

    def _exposeShapes(self):
        return self._cpPolyShapes

    def distanceFromPoint(self, point):
        d, _ = self._cpSensor.point_query(point)
        return d

    def getArea(self):
        return self._area

    polys = property(getPolys)
    vertices = property(getVertices)
    friction = property(getFriction, setFriction)
    elasticity = property(getElasticity, setElasticity)
    area = property(getArea)


class PGCompound(PGObject):

    def __init__(self, name, space, polygons, density = DEFAULT_DENSITY,
                 elasticity=DEFAULT_ELASTICITY, friction=DEFAULT_FRICTION,color=DEFAULT_COLOR):
        PGObject.__init__(self, name, "Compound", space, color, density, friction, elasticity)

        self._area = 0
        self.polylist = []
        self._cpShapes = []
        # If it's static, add polygons inplace
        if density == 0:
            polyCents = []
            areas = []
            for vertices in polygons:
                polyCents.append(centroidForPoly(vertices))
                areas.append(areaForPoly(vertices))
                sh = pm.Poly(space.static_body, vertices)
                sh.elasticity = elasticity
                sh.friction = friction
                sh.collision_type = COLTYPE_SOLID
                sh.name = name
                space.add(sh)
                self._cpShapes.append(sh)
                self.polylist.append([pm.Vec2d(p) for p in vertices])

            gx = gy = 0
            for pc, a in zip(polyCents, areas):
                gx += pc[0] * a
                gy += pc[1] * a
                self._area += a
            gx /= self._area
            gy /= self._area
            loc = pm.Vec2d(gx, gy)
            self.pos = np.array([gx, gy])

        else:
            polyCents = []
            areas = []
            for i in range(len(polygons)):
                vertices = polygons[i]
                polyCents.append(centroidForPoly(vertices))
                vertices = recenterPoly(vertices)
                polygons[i] = vertices
                areas.append(areaForPoly(vertices))
            gx = gy = 0
            for pc, a in zip(polyCents, areas):
                gx += pc[0] * a
                gy += pc[1] * a
                self._area += a
            gx /= self._area
            gy /= self._area
            loc = pm.Vec2d(gx, gy)
            imom = 0
            for pc, a, verts in zip(polyCents, areas, polygons):
                pos = pm.Vec2d(pc[0] - loc.x, pc[1] - loc.y)
                imom += pm.moment_for_poly(density*a, vertices, pos)
                rcverts = [pm.Vec2d([p[0]+pos.x, p[1]+pos.y]) for p in verts]
                self._cpShapes.append(pm.Poly(None, rcverts))
                self.polylist.append(rcverts)
            mass = self._area*density
            self._cpBody = pm.Body(mass, imom)
            for sh in self._cpShapes:
                sh.body = self._cpBody
                sh.elasticity = elasticity
                sh.friction = friction
                sh.collision_type = COLTYPE_SOLID
                sh.name = name
                space.add(sh)
            self._cpBody.position = loc
            space.add(self._cpBody)

    def getPolys(self):
        if self.isStatic():
            rpolys = []
            for poly in self.polylist:
                rpolys.append([np.array(p) for p in poly])
            return rpolys
        else:
            pos = self.position
            rot = self.rotation
            rpolys = []
            for poly in self.polylist:
                rpolys.append([np.array(p.rotated(rot) + pos) for p in poly])
            return rpolys

    def getArea(self):
        return self._area

    def getFriction(self):
        return self._cpShapes[0].friction

    def setFriction(self, val):
        assert val >= 0, "Friction must be greater than or equal to 0"
        for s in self._cpShapes:
            s.friction = val

    def getElasticity(self):
        return self._cpShapes[0].elasticity

    def setElasticity(self, val):
        assert val >= 0, "Elasticity must be greater than or equal to 0"
        for s in self._cpShapes:
            s.elasticity = val

    def _exposeShapes(self):
        return self._cpShapes

    def getPos(self):
        if self.isStatic():
            return self.pos
        else:
            p = self._cpBody.position
            return np.array([p.x, p.y])

    polys = property(getPolys)
    friction = property(getFriction, setFriction)
    elasticity = property(getElasticity, setElasticity)
    area = property(getArea)

    def distanceFromPoint(self, point):
        dists = [s.point_query(point) for s in self._cpShapes]
        return min(dists)


class PGGoal(PGObject):

    def __init__(self, name, space, vertices, color):
        PGObject.__init__(self, name, "Goal", space, color, 0, 0, 0)
        self._cpShape = pm.Poly(space.static_body, vertices)
        self._cpShape.sensor = True
        self._cpShape.collision_type = COLTYPE_SENSOR
        self._cpShape.name = name
        space.add(self._cpShape)

    def getVertices(self):
        verts = [np.array(v) for v in self._cpShape.get_vertices()]
        verts.reverse()
        return verts

    def pointIn(self,p):
        v = pm.Vec2d(p[0], p[1])
        return self._cpShape.point_query(v)

    vertices = property(getVertices)


class PGBlocker(PGObject):

    def __init__(self, name, space, vertices, color):
        PGObject.__init__(self, name, "Blocker", space, color, 0, 0, 0)
        self._cpShape = pm.Poly(space.static_body, vertices)
        self._cpShape.sensor = True
        self._cpShape.collision_type = COLTYPE_BLOCKED
        self._cpShape.name = name
        space.add(self._cpShape)

    def getVertices(self):
        verts = [np.array(v) for v in self._cpShape.get_vertices()]
        verts.reverse()
        return verts

    def pointIn(self, p):
        v = pm.Vec2d(p[0], p[1])
        return self._cpShape.point_query(v)

    vertices = property(getVertices)
