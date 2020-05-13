/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/*
 * Constants used throughout
 */

cp = require('chipmunk');

DEFAULT_DENSITY = 1.;
DEFAULT_ELASTICITY = 0.5;
DEFAULT_FRICTION = 0.5;
DEFAULT_COLOR = 'black';

COLTYPE_SOLID = 100;
COLTYPE_SENSOR = 101;
COLTYPE_PLACED = 102;
COLTYPE_BLOCKED = 103;
COLTYPE_CHECKER = 104;


/*
 *
 * Helper functions
 *
 */

function AssertException(message) {
  this.message = message;
}
AssertException.prototype.toString = function() {
  return 'AssertException: ' + this.message;
};

function assert(exp, message) {
  if (!exp) {
    throw new AssertException(message);
  }
}

function isFunction(obj) {
  var getType = {};
  return obj && getType.toString.call(obj) === '[object Function]';
};

function _debugCollisionHandler(arb, space) {
  console.log('hit');
};

function _emptyCollisionHandler(arb, space) {
  return;
};

function _emptyObjectHandler(o1, o2) {
  return;
};

// Extracts the object names from a collision arbiter
function resolveArbiter(arb) {
  var shs = arb.getShapes();
  var o1 = shs[0],
    o2 = shs[1];
  return [o1.name, o2.name];
};

// Functions outside of the PGWorld object for callbacks
function ssbeg(arb, space, pgworld) {
  pgworld._solidSolidBegin(arb, space, pgworld);
  return true;
};

function sspre(arb, space, pgworld) {
  pgworld._solidSolidPre(arb, space, pgworld);
  return true;
};

function sspost(arb, space, pgworld) {
  pgworld._solidSolidPost(arb, space, pgworld);
  return true;
};

function ssend(arb, space, pgworld) {
  pgworld._solidSolidEnd(arb, space, pgworld);
  return true;
};

function sgbeg(arb, space, pgworld) {
  pgworld._solidGoalBegin(arb, space, pgworld);
  return false;
};

function sgend(arb, space, pgworld) {
  pgworld._solidGoalEnd(arb, space, pgworld);
  return false;
};

// Rotate a point by an angle around (0,0)
function angRotate(p, a) {
  var s = Math.sin(a),
    c = Math.cos(a);

  return ([p[0] * c - p[1] * s, p[0] * s + p[1] * c]);
};

// Reverse a flat array of 2-d points
function rev2d(arr) {
  var ret = [];
  for (var i = arr.length - 2; i >= 0; i -= 2) {
    ret.push(arr[i], arr[i + 1]);
  }
  return (ret);
};

// Hack: pulled from chipmunk.js
var vcross2 = function(x1, y1, x2, y2) {
  return x1 * y2 - y1 * x2;
};
var polyValidate = function(verts) {
  var len = verts.length;
  for (var i = 0; i < len; i += 2) {
    var ax = verts[i];
    var ay = verts[i + 1];
    var bx = verts[(i + 2) % len];
    var by = verts[(i + 3) % len];
    var cx = verts[(i + 4) % len];
    var cy = verts[(i + 5) % len];

    //if(vcross(vsub(b, a), vsub(c, b)) > 0){
    if (vcross2(bx - ax, by - ay, cx - bx, cy - by) > 0) {
      return false;
    }
  }

  return true;
};

// A function for turning a set of segments into a set of poly shapes
// (Hack needed to get around the fact that cp has no seg-seg collisions)
var isleft = function(spt, ept, testpt) {
  var seg1 = [ept[0] - spt[0], ept[1] - spt[1]];
  var seg2 = [testpt[0] - spt[0], testpt[1] - spt[1]];
  var cross = seg1[0] * seg2[1] - seg1[1] * seg2[0];
  return cross > 0;
};

var segs2Poly = function(seglist, r) {
  assert(seglist.length > 7 && seglist.length % 2 === 0, "Need at least four points in flat structure to poly-ize");

  // Turn the segments into cp vectors for built-in computation
  var vlist = [];
  for (var i = 0; i < seglist.length - 1; i += 2) {
    vlist.push(new cp.v(seglist[i], seglist[i + 1]));
  }

  // Start by figuring out the initial edge (ensure ccw winding)
  var iseg = cp.v.sub(vlist[1], vlist[0]);
  var ipt = vlist[0];
  var iang = cp.v.toangle(iseg);
  var prev1, prev2;
  if (iang <= (-Math.PI / 4) && iang >= (-Math.PI * 3 / 4)) {
    // Going downwards
    prev1 = [ipt.x - r, ipt.y];
    prev2 = [ipt.x + r, ipt.y];
  } else if (iang >= (Math.PI / 4) && iang <= (Math.PI * 3 / 4)) {
    // Going upwards
    prev1 = [ipt.x + r, ipt.y];
    prev2 = [ipt.x - r, ipt.y];
  } else if (iang >= (-Math.PI / 4) && iang <= (Math.PI / 4)) {
    // Going rightwards
    prev1 = [ipt.x, ipt.y - r];
    prev2 = [ipt.x, ipt.y + r];
  } else {
    // Going leftwards
    prev1 = [ipt.x, ipt.y + r];
    prev2 = [ipt.x, ipt.y - r];
  }

  var polylist = []; // The ultimate thing to return

  var pi, pim, pip, sm, sp, angm, angp, angi, angn, unitn, xdiff, ydiff, next3, next4;
  for (var i = 1; i < vlist.length - 1; i++) {
    pi = vlist[i];
    pim = vlist[i - 1];
    pip = vlist[i + 1];
    sm = cp.v.sub(pim, pi);
    sp = cp.v.sub(pip, pi);
    // Get the angle of intersection between the two lines, constrained to [0, 2pi)
    angm = cp.v.toangle(sm);
    angp = cp.v.toangle(sp);
    angi = (angm - angp) % (2 * Math.PI);
    // Find the midpoint of this angle and turn it back into a unit vector
    angn = (angp + (angi / 2)) % (2 * Math.PI);
    if (angn < 0) {
      angn += 2 * Math.PI;
    }
    unitn = cp.v.forangle(angn);
    //next3 = [pi.x + r*unitn.x, pi.y + r*unitn.y];
    //next4 = [pi.x - r*unitn.x, pi.y - r*unitn.y];
    xdiff = unitn.x >= 0 ? r : -r;
    ydiff = unitn.y >= 0 ? r : -r;
    next3 = [pi.x + xdiff, pi.y + ydiff];
    next4 = [pi.x - xdiff, pi.y - ydiff];
    // Ensure appropriate winding -- next3 should be on the left of next4
    if (isleft(prev2, next3, next4)) {
      var tmp = next4;
      next4 = next3;
      next3 = tmp;
    }
    polylist.push([prev1[0], prev1[1], prev2[0], prev2[1], next3[0], next3[1], next4[0], next4[1]]);
    prev1 = next4;
    prev2 = next3;
  }

  // Finish by figuring out the final edge
  var fseg = cp.v.sub(vlist[vlist.length - 2], vlist[vlist.length - 1]);
  var fpt = vlist[vlist.length - 1];
  var fang = cp.v.toangle(fseg);
  if (fang <= (-Math.PI / 4) && fang >= (-Math.PI * 3 / 4)) {
    // Coming from downwards
    next3 = [fpt.x - r, fpt.y];
    next4 = [fpt.x + r, fpt.y];
  } else if (fang >= (Math.PI / 4) && fang <= (Math.PI * 3 / 4)) {
    // Coming from upwards
    next3 = [fpt.x + r, fpt.y];
    next4 = [fpt.x - r, fpt.y];
  } else if (fang >= (-Math.PI / 4) && fang <= (Math.PI / 4)) {
    // Coming from rightwards
    next3 = [fpt.x, fpt.y - r];
    next4 = [fpt.x, fpt.y + r];
  } else {
    // Coming from leftwards
    next3 = [fpt.x, fpt.y + r];
    next4 = [fpt.x, fpt.y - r];
  }
  polylist.push([prev1[0], prev1[1], prev2[0], prev2[1], next3[0], next3[1], next4[0], next4[1]]);
  return polylist;
};

/*
 * The objects that get placed in the game world -- wrappers around Chipmunk
 * to set these
 *
 * Wrapper functions include:
 *
 * Constructor PGObject(name, type, space) : helps in object creation
 * bool isStatic() : returns whether object is a static shape
 * [float, float] getPos(): returns the position of a non-static object
 * void setPos([float, float]) : sets the position of a non-static object
 * float getRot(): returns the angular rotation of a non-static object
 * void setRot(float): sets the angular rotation of a non-static object
 * fload getMass(): returns the mass of the object (zero if static)
 */

PGObject = function(name, type, space, color, density) {
  var legalTypes = ['Ball', 'Poly', 'Segment', 'Container', 'Compound', 'Goal', 'Blocker']; // To add compound shapes later
  assert(legalTypes.indexOf(type) > -1, "Invalid 'type' of object");
  this.name = name;
  this.type = type;
  this.space = space;
  this.color = color;
  this.density = density;
};

PGObject.prototype.isStatic = function() {
  return this.cpBody === null;
};

PGObject.prototype.getPos = function() {
  assert(!this.isStatic(), "Static bodies do not have a position");
  var p = this.cpBody.getPos();
  return [p.x, p.y];
};

PGObject.prototype.setPos = function(p) {
  assert(!this.isStatic(), "Cannot set the position of static objects");
  assert(p.length === 2, "Position requires array of length 2");
  var v = new cp.v(p[0], p[1]);
  this.cpBody.setPos(v);
};

PGObject.prototype.getVel = function() {
  assert(!this.isStatic(), "Static bodies do not have a velocity");
  var p = this.cpBody.getVel();
  return [p.x, p.y];
}

PGObject.prototype.setVel = function(v) {
  assert(!this.isStatic(), "Cannot set the velocity of static objects");
  assert(v.length === 2, "Velocity requires array of length 2");
  var vct = new cp.v(v[0], v[1]);
  this.cpBody.setVel(vct);
};

PGObject.prototype.getRot = function() {
  assert(!this.isStatic(), "Static bodies do not have a rotation");
  return this.cpBody.a;
};

PGObject.prototype.setRot = function(a) {
  assert(!this.isStatic(), "Static bodies do not have a rotation");
  this.cpBody.setAngle(a);
};

PGObject.prototype.getMass = function() {
  if (this.isStatic()) return 0;
  else return this.cpBody.m;
};

// Create a generic polygon object

PGPoly = function(name, space, vertices, density, elasticity, friction, color) {
  var density = typeof density !== 'undefined' ? density : DEFAULT_DENSITY;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : DEFAULT_ELASTICITY;
  var friction = typeof friction !== 'undefined' ? friction : DEFAULT_FRICTION;
  var color = typeof color !== 'undefined' ? color : DEFAULT_COLOR;

  // Flatten the vertices
  var fvert = [];
  for (var i = 0; i < vertices.length; i++) {
    var v = vertices[i];
    fvert.push(v[0]);
    fvert.push(v[1]);
  }

  PGObject.call(this, name, "Poly", space, color, density);

  var loc = cp.centroidForPoly(fvert);
  cp.recenterPoly(fvert);
  var area = cp.areaForPoly(fvert);
  var mass = density * area;
  var imom = cp.momentForPoly(mass, fvert, cp.vzero);

  if (mass === 0) {
    this.cpBody = null;
    debugger;
    this.cpShape = new cp.PolyShape(space.staticBody, fvert, loc);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    space.addShape(this.cpShape);
  } else {
    this.cpBody = new cp.Body(mass, imom);
    this.cpShape = new cp.PolyShape(this.cpBody, fvert, cp.vzero);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    this.cpBody.setPos(new cp.v(loc.x, loc.y));
    space.addBody(this.cpBody);
    space.addShape(this.cpShape);
  }
};

PGPoly.prototype = Object.create(PGObject.prototype);

PGPoly.prototype.getVertices = function() {
  var verts = [];

  if (this.isStatic()) {
    for (var i = 0; i < this.cpShape.verts.length - 1; i += 2) {
      var v = [this.cpShape.verts[i], this.cpShape.verts[i + 1]];
      verts.push(v);
    }
  } else {
    var pos = this.getPos();
    var rot = this.getRot();
    for (var i = 0; i < this.cpShape.verts.length - 1; i += 2) {
      var v = [this.cpShape.verts[i], this.cpShape.verts[i + 1]];
      v = angRotate(v, rot);
      verts.push([v[0] + pos[0], v[1] + pos[1]]);
    }
  }
  return verts;
};

PGPoly.prototype.getArea = function() {
  return cp.areaForPoly(this.getVertices());
};

// Overload getPos to allow for static objects too
PGPoly.prototype.getPos = function() {
  if (this.isStatic()) return cp.centroidForPoly(this.getVertices());
  else {
    var v = this.cpBody.getPos();
    return [v.x, v.y];
  }
};

// Create a circular object

PGBall = function(name, space, position, radius, density, elasticity, friction, color) {
  var density = typeof density !== 'undefined' ? density : DEFAULT_DENSITY;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : DEFAULT_ELASTICITY;
  var friction = typeof friction !== 'undefined' ? friction : DEFAULT_FRICTION;
  var color = typeof color !== 'undefined' ? color : DEFAULT_COLOR;

  PGObject.call(this, name, "Ball", space, color, density);

  var area = Math.PI * radius * radius;
  var mass = density * area;
  var imom = cp.momentForCircle(mass, 0, radius, cp.vzero);

  var p = new cp.v(position[0], position[1]);

  if (mass === 0) {
    this.cpBody = null;
    this.cpShape = new cp.CircleShape(space.staticBody, radius, p);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    space.addShape(this.cpShape);
  } else {
    this.cpBody = new cp.Body(mass, imom);
    this.cpShape = new cp.CircleShape(this.cpBody, radius, cp.vzero);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    this.cpBody.setPos(p);
    space.addBody(this.cpBody);
    space.addShape(this.cpShape);
  }
};

PGBall.prototype = Object.create(PGObject.prototype);

PGBall.prototype.getRadius = function() {
  return this.cpShape.r;
};

PGBall.prototype.getArea = function() {
  var r = this.getRadius();
  return Math.PI * r * r;
};

// Overload getPos to allow for static objects too
PGBall.prototype.getPos = function() {
  var v;
  if (this.isStatic()) {
    v = this.cpShape.tc;
  } else {
    v = this.cpBody.getPos();
  }
  return [v.x, v.y];
};

// Create an object that consists of a single segment

PGSeg = function(name, space, p1, p2, width, density, elasticity, friction, color) {
  var density = typeof density !== 'undefined' ? density : DEFAULT_DENSITY;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : DEFAULT_ELASTICITY;
  var friction = typeof friction !== 'undefined' ? friction : DEFAULT_FRICTION;
  var color = typeof color !== 'undefined' ? color : DEFAULT_COLOR;

  PGObject.call(this, name, "Segment", space, color, density);

  var v1 = new cp.v(p1[0], p1[1]);
  var v2 = new cp.v(p2[0], p2[1]);
  var r = width / 2;
  this.r = r;

  var area = cp.areaForSegment(v1, v2, r);
  var mass = density * area;
  var imom = cp.momentForSegment(mass, v1, v2);

  if (mass === 0) {
    this.cpBody = null;
    this.cpShape = new cp.SegmentShape(space.staticBody, v1, v2, r);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    space.addShape(this.cpShape);
  } else {
    this.cpBody = new cp.Body(mass, imom);
    var pos = new cp.v((v1.x + v2.x) / 2, (v1.y + v2.y) / 2);
    v1 = cp.v.sub(v1, pos);
    v2 = cp.v.sub(v2, pos);
    this.cpShape = new cp.SegmentShape(this.cpBody, v1, v2, r);
    this.cpShape.setElasticity(elasticity);
    this.cpShape.setFriction(friction);
    this.cpShape.setCollisionType(COLTYPE_SOLID);
    this.cpShape.name = name;
    this.cpBody.setPos(pos);
    space.addBody(this.cpBody);
    space.addShape(this.cpShape);
  }
};

PGSeg.prototype = Object.create(PGObject.prototype);

PGSeg.prototype.getPoints = function() {
  var p1, p2;
  var v1 = this.cpShape.a,
    v2 = this.cpShape.b;

  if (this.isStatic()) {
    p1 = [v1.x, v1.y];
    p2 = [v2.x, v2.y];
  } else {
    var pos = this.getPos();
    var rot = this.getRot();
    var tp1 = angRotate([v1.x, v1.y], rot);
    var tp2 = angRotate([v2.x, v2.y], rot);
    p1 = [tp1[0] + pos[0], tp1[1] + pos[1]];
    p2 = [tp2[0] + pos[0], tp2[1] + pos[1]];
  }
  return [p1, p2];
};

// An object that contains a sensor within it

PGContainer = function(name, space, ptlist, width, density, elasticity, friction, color) {
  var density = typeof density !== 'undefined' ? density : DEFAULT_DENSITY;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : DEFAULT_ELASTICITY;
  var friction = typeof friction !== 'undefined' ? friction : DEFAULT_FRICTION;
  var color = typeof color !== 'undefined' ? color : DEFAULT_COLOR;

  PGObject.call(this, name, "Container", space, color, density);

  var r = width / 2;
  this.r = r;
  // Flatten the vertices
  var fvert = [];
  for (var i = 0; i < ptlist.length; i++) {
    var v = ptlist[i];
    fvert.push(v[0]);
    fvert.push(v[1]);
  }
  var loc = cp.centroidForPoly(fvert);
  if (density !== 0) cp.recenterPoly(fvert);
  this.seglist = [];
  for (var i = 0; i < fvert.length - 1; i += 2) {
    this.seglist.push(new cp.v(fvert[i], fvert[i + 1]));
  }

  this.area = Math.PI * r * r;
  var imom = 0;
  for (var i = 0; i < this.seglist.length - 1; i++) {
    var v1 = this.seglist[i],
      v2 = this.seglist[i + 1];
    var larea = 2 * r * cp.v.dist(v1, v2);
    this.area += larea;
    imom += cp.momentForSegment(larea * density, v1, v2);
  }

  var mass = density * this.area;

  var uBody;
  if (mass === 0) {
    this.cpBody = null;
    uBody = space.staticBody;
  } else {
    this.cpBody = uBody = new cp.Body(mass, imom);
    space.addBody(this.cpBody);
  }

  // Add the segment shapes
  this.cpPolyShapes = [];
  this.polylist = segs2Poly(fvert, r);

  for (var i = 0; i < this.polylist.length; i++) {
    var pshp = new cp.PolyShape(uBody, this.polylist[i], cp.vzero);
    pshp.setElasticity(elasticity);
    pshp.setFriction(friction);
    pshp.setCollisionType(COLTYPE_SOLID);
    pshp.name = name;
    this.cpPolyShapes.push(pshp);
    space.addShape(pshp);
  }

  // Add the sensor shape
  //var cvh = cp.convexHull(fvert, []);

  if (!polyValidate(fvert)) fvert = rev2d(fvert);

  this.cpSensor = new cp.PolyShape(uBody, fvert, cp.vzero);
  this.cpSensor.sensor = true;
  this.cpSensor.setCollisionType(COLTYPE_SENSOR);
  this.cpSensor.name = name;
  space.addShape(this.cpSensor);
  if (mass !== 0) this.cpBody.setPos(loc);
};

PGContainer.prototype = Object.create(PGObject.prototype);

PGContainer.prototype.getPolys = function() {
  var polys = [];

  if (this.isStatic()) {
    for (var i = 0; i < this.polylist.length; i++) {
      var tpol = [];
      for (var j = 0; j < this.polylist[i].length; j += 2) {
        tpol.push([this.polylist[i][j], this.polylist[i][j + 1]]);
      }
      polys.push(tpol);
    }
  } else {
    var pos = this.getPos();
    var rot = this.getRot();
    for (var i = 0; i < this.polylist.length; i++) {
      var tpol = [];
      for (var j = 0; j < this.polylist[i].length; j += 2) {
        var p = angRotate([this.polylist[i][j], this.polylist[i][j + 1]], rot);
        tpol.push([p[0] + pos[0], p[1] + pos[1]]);
      }
      polys.push(tpol);
    }
  }
  return polys;

};

PGContainer.prototype.getVertices = function() {
  var verts = [];
  var b = this.cpBody;
  for (var i = 0; i < this.seglist.length; i++) {
    var s = this.seglist[i];
    if (b === null) {
      verts.push([s.x, s.y]);
    } else {
      var r = this.cpBody.local2World(s);
      verts.push([r.x, r.y]);
    }
  }
  return verts;
};

PGContainer.prototype.pointIn = function(p) {
  var v = new cp.v(p[0], p[1]);
  return this.cpSensor.pointQuery(v);
};

// A shape composed of multiple convex polygons
PGCompound = function(name, space, polygons, density, elasticity, friction, color) {
  var density = typeof density !== 'undefined' ? density : DEFAULT_DENSITY;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : DEFAULT_ELASTICITY;
  var friction = typeof friction !== 'undefined' ? friction : DEFAULT_FRICTION;
  var color = typeof color !== 'undefined' ? color : DEFAULT_COLOR;

  PGObject.call(this, name, "Compound", space, color, density);
  this.area = 0;
  this.polylist = [];
  // If it's static, just add the polygons in place
  if (density === 0) {
    this.cpShapes = [];
    this.cpBody = null;
    for (var i = 0; i < polygons.length; i++) {
      var vertices = polygons[i];
      // Flatten the vertices
      var fvert = [];
      for (var j = 0; j < vertices.length; j++) {
        var v = vertices[j];
        fvert.push(v[0]);
        fvert.push(v[1]);
      }
      var sh = new cp.PolyShape(space.staticBody, fvert, cp.vzero);
      sh.setElasticity(elasticity);
      sh.setFriction(friction);
      sh.setCollisionType(COLTYPE_SOLID);
      sh.name = name;
      space.addShape(sh);
      this.cpShapes.push(sh);
      this.area += cp.areaForPoly(fvert);
      this.polylist.push(fvert);
    }
  } else {
    var polyCents = [];
    var flattened = [];
    var areas = [];
    // Recenter polygons around their own centers, get out areas & locs
    for (var i = 0; i < polygons.length; i++) {
      var vertices = polygons[i];
      // Flatten the vertices
      var fvert = [];
      for (var j = 0; j < vertices.length; j++) {
        var v = vertices[j];
        fvert.push(v[0]);
        fvert.push(v[1]);
      }

      polyCents.push(cp.centroidForPoly(fvert));
      cp.recenterPoly(fvert);
      flattened.push(fvert);
      areas.push(cp.areaForPoly(fvert));
    }
    // Calculate the grand center of mass
    var gx = 0,
      gy = 0;
    for (var i = 0; i < polyCents.length; i++) {
      gx += polyCents[i].x * areas[i];
      gy += polyCents[i].y * areas[i];
      this.area += areas[i];
    }
    gx /= this.area;
    gy /= this.area;
    var loc = [gx, gy];
    // Go through each of the shapes and recenter around the grand mean
    this.cpShapes = [];
    var imom = 0;
    for (var i = 0; i < flattened.length; i++) {
      fverts = flattened[i];
      var rcverts = [];
      var pos = new cp.v(polyCents[i].x - loc[0], polyCents[i].y - loc[1]);
      for (var j = 0; j < fverts.length; j++) {
        rcverts.push(fverts[j] + (j % 2 ? pos.y : pos.x));
      }
      imom += cp.momentForPoly(density * areas[i], fverts, pos);
      this.cpShapes.push(new cp.PolyShape(null, fverts, pos));
      this.polylist.push(rcverts);
    };
    // Form the body and attach each of the shapes
    var mass = this.area * density;
    this.cpBody = new cp.Body(mass, imom);
    for (var i = 0; i < this.cpShapes.length; i++) {
      this.cpShapes[i].setBody(this.cpBody);
      this.cpShapes[i].setElasticity(elasticity);
      this.cpShapes[i].setFriction(friction);
      this.cpShapes[i].setCollisionType(COLTYPE_SOLID);
      this.cpShapes[i].name = name;
      space.addShape(this.cpShapes[i]);
    }
    this.cpBody.setPos(new cp.v(loc[0], loc[1]));
    space.addBody(this.cpBody);
  }
};

PGCompound.prototype = Object.create(PGObject.prototype);

PGCompound.prototype.getPolys = function() {
  var polys = [];

  if (this.isStatic()) {
    for (var i = 0; i < this.polylist.length; i++) {
      var tpol = [];
      for (var j = 0; j < this.polylist[i].length; j += 2) {
        tpol.push([this.polylist[i][j], this.polylist[i][j + 1]]);
      }
      polys.push(tpol);
    }
  } else {
    var pos = this.getPos();
    var rot = this.getRot();
    for (var i = 0; i < this.polylist.length; i++) {
      var tpol = [];
      for (var j = 0; j < this.polylist[i].length; j += 2) {
        var p = angRotate([this.polylist[i][j], this.polylist[i][j + 1]], rot);
        tpol.push([p[0] + pos[0], p[1] + pos[1]]);
      }
      polys.push(tpol);
    }
  }
  return polys;

};

// A static object that just creates a sensor region
PGGoal = function(name, space, vertices, color) {
  // Flatten the vertices
  var fvert = [];
  for (var i = 0; i < vertices.length; i++) {
    var v = vertices[i];
    fvert.push(v[0]);
    fvert.push(v[1]);
  }

  PGObject.call(this, name, "Goal", space, color, 0);
  this.cpBody = null;
  this.cpShape = new cp.PolyShape(space.staticBody, fvert, cp.vzero);
  this.cpShape.sensor = true;
  this.cpShape.setCollisionType(COLTYPE_SENSOR);
  this.cpShape.name = name;
  space.addShape(this.cpShape);
};

PGGoal.prototype = Object.create(PGObject.prototype);

PGGoal.prototype.getVertices = function() {
  var verts = [];

  for (var i = 0; i < this.cpShape.verts.length - 1; i += 2) {
    var v = [this.cpShape.verts[i], this.cpShape.verts[i + 1]];
    verts.push(v);
  }

  return verts;
};

PGGoal.prototype.pointIn = function(p) {
  var v = new cp.v(p[0], p[1]);
  return this.cpShape.pointQuery(v);
};

PGBlocker = function(name, space, vertices, color) {
  // Flatten the vertices
  var fvert = [];
  for (var i = 0; i < vertices.length; i++) {
    var v = vertices[i];
    fvert.push(v[0]);
    fvert.push(v[1]);
  }

  PGObject.call(this, name, "Blocker", space, color, 0);
  this.cpBody = null;
  this.cpShape = new cp.PolyShape(space.staticBody, fvert, cp.vzero);
  this.cpShape.sensor = true;
  this.cpShape.setCollisionType(COLTYPE_BLOCKED);
  this.cpShape.name = name;
  space.addShape(this.cpShape);
};

PGBlocker.prototype = Object.create(PGObject.prototype);

PGBlocker.prototype.getVertices = function() {
  var verts = [];

  for (var i = 0; i < this.cpShape.verts.length - 1; i += 2) {
    var v = [this.cpShape.verts[i], this.cpShape.verts[i + 1]];
    verts.push(v);
  }

  return verts;
};

PGBlocker.prototype.pointIn = function(p) {
  var v = new cp.v(p[0], p[1]);
  return this.cpShape.pointQuery(v);
};


/*
 *
 * Conditions -- the objects that check whether "success" is achieved
 */

PGCond_AnyInGoal = function(goalname, duration, parent, exclusions) {
  var exclusions = typeof(exclusions) !== 'undefined' ? exclusions : [];

  this.type = "AnyInGoal";
  this.won = false;
  this.goal = goalname;
  this.excl = exclusions;
  this.dur = duration;
  this.ins = {};
  this.hasTime = true;
  this.parent = parent;

};

PGCond_AnyInGoal.prototype._goesIn = function(obj, goal, me) {
  if (goal.name === me.goal &&
    !(obj.name in me.ins) &&
    me.excl.indexOf(obj.name) === -1) {

    me.ins[obj.name] = me.parent.time;

  }
};

PGCond_AnyInGoal.prototype._goesOut = function(obj, goal, me) {
  if (goal.name === me.goal &&
    (obj.name in me.ins) &&
    !(goal.pointIn(obj.getPos()))) {

    delete me.ins[obj.name];

  }
};

PGCond_AnyInGoal.prototype.attachHooks = function() {
  var me = this;
  me.parent.setGoalCollisionBegin(function(o, g) {
    me._goesIn(o, g, me);
  });
  me.parent.setGoalCollisionEnd(function(o, g) {
    me._goesOut(o, g, me);
  });
};

PGCond_AnyInGoal.prototype.remainingTime = function() {
  if (Object.keys(this.ins).length === 0) return null;
  var mintime = this.parent.time;
  for (var k in this.ins) {
    if (this.ins[k] < mintime) mintime = this.ins[k];
  }
  var curin = this.parent.time - mintime;
  return Math.max(this.dur - curin, 0);
};

PGCond_AnyInGoal.prototype.isWon = function() {
  return this.remainingTime() === 0;
};

// Like AnyInGoal but requires a specific object to get there
PGCond_SpecificInGoal = function(goalname, objname, duration, parent) {

  this.type = "SpecificInGoal";
  this.won = false;
  this.goal = goalname;
  this.obj = objname;
  this.dur = duration;
  this.tin = 0;
  this.hasTime = true;
  this.parent = parent;

};

PGCond_SpecificInGoal.prototype._goesIn = function(obj, goal, me) {
  if (goal.name === me.goal &&
    (obj.name === me.obj)) {
    me.tin = me.parent.time;
  }
};

PGCond_SpecificInGoal.prototype._goesOut = function(obj, goal, me) {
  if (goal.name === me.goal &&
    (obj.name === me.obj) &&
    !(goal.pointIn(obj.getPos()))) {

    me.tin = 0;

  }
};

PGCond_SpecificInGoal.prototype.attachHooks = function() {
  var me = this;
  me.parent.setGoalCollisionBegin(function(o, g) {
    me._goesIn(o, g, me);
  });
  me.parent.setGoalCollisionEnd(function(o, g) {
    me._goesOut(o, g, me);
  });
};

PGCond_SpecificInGoal.prototype.remainingTime = function() {
  if (this.tin === 0) return null;
  var curin = this.parent.time - this.tin;
  return Math.max(this.dur - curin, 0);
};

PGCond_SpecificInGoal.prototype.isWon = function() {
  return this.remainingTime() === 0;
};

PGCond_AnyTouch = function(objname, duration, parent) {
  this.type = "AnyTouch";
  this.won = false;
  this.goal = objname;
  this.dur = duration;
  this.tin = 0;
  this.hasTime = true;
  this.parent = parent;
};

PGCond_AnyTouch.prototype._beginTouch = function(obj, goal, me) {
  if (obj.name === me.goal | goal.name === me.goal) {
    me.tin = me.parent.time;
  }
};

PGCond_AnyTouch.prototype._endTouch = function(obj, goal, me) {
  if (obj.name === me.goal | goal.name === me.goal) {
    me.tin = 0;
  }
};

PGCond_AnyTouch.prototype.attachHooks = function() {
  var me = this;
  me.parent.setSolidCollisionBegin(function(o, g) {
    me._beginTouch(o, g, me);
  });
  me.parent.setSolidCollisionEnd(function(o, g) {
    me._endTouch(o, g, me);
  });
};

PGCond_AnyTouch.prototype.remainingTime = function() {
  if (this.tin === 0) return null;
  var curin = this.parent.time - this.tin;
  return Math.max(this.dur - curin, 0);
};

PGCond_AnyTouch.prototype.isWon = function() {
  return this.remainingTime() === 0;
};

PGCond_SpecificTouch = function(objname1, objname2, duration, parent) {
  this.type = "SpecificTouch";
  this.won = false;
  this.o1 = objname1;
  this.o2 = objname2;
  this.dur = duration;
  this.tin = 0;
  this.hasTime = true;
  this.parent = parent;
};

PGCond_SpecificTouch.prototype._beginTouch = function(obj1, obj2, me) {
  if ((obj1.name === me.o1 & obj2.name === me.o2) | (obj1.name === me.o2 & obj2.name === me.o1)) {
    me.tin = me.parent.time;
  }
};

PGCond_SpecificTouch.prototype._endTouch = function(obj1, obj2, me) {
  if ((obj1.name === me.o1 & obj2.name === me.o2) | (obj1.name === me.o2 & obj2.name === me.o1)) {
    me.tin = 0;
  }
};

PGCond_SpecificTouch.prototype.attachHooks = function() {
  var me = this;
  me.parent.setSolidCollisionBegin(function(o, g) {
    me._beginTouch(o, g, me);
  });
  me.parent.setSolidCollisionEnd(function(o, g) {
    me._endTouch(o, g, me);
  });
};

PGCond_SpecificTouch.prototype.remainingTime = function() {
  if (this.tin === 0) return null;
  var curin = this.parent.time - this.tin;
  return Math.max(this.dur - curin, 0);
};

PGCond_SpecificTouch.prototype.isWon = function() {
  return this.remainingTime() === 0;
};


/*
 * PGWorld: the meat of what gets exposed
 * Most functions should be run solely through calls on a PGWorld object
 *
 */

/*
 *
 * @param {[num, num]} dimensions
 * @param {float} gravity
 * @param {[bool, bool, bool, bool]} closed_ends
 * @param {float} basic_timestep
 * @param {float} def_density
 * @param {float} def_elasticity
 * @param {float} def_friction
 * @param {type} bk_col
 * @param {type} def_col
 * @returns {PGWorld}
 */

PGWorld = function(dimensions, gravity, closed_ends, basic_timestep,
  def_density, def_elasticity, def_friction, bk_col, def_col) {

  var basic_timestep = typeof basic_timestep !== 'undefined' ? basic_timestep : .01;
  var closed_ends = typeof closed_ends !== 'undefined' ? closed_ends : [true, true, true, true];
  this.def_density = typeof def_density !== 'undefined' ? def_density : DEFAULT_DENSITY;
  this.def_elasticity = typeof def_elasticity !== 'undefined' ? def_elasticity : DEFAULT_ELASTICITY;
  this.def_friction = typeof def_friction !== 'undefined' ? def_friction : DEFAULT_FRICTION;
  this.bk_col = typeof bk_col !== 'undefined' ? bk_col : 'white';
  this.def_col = typeof def_col !== 'undefined' ? def_col : 'black';

  assert(closed_ends.length === 4, "closed_ends must be a length 4 boolean array (l,b,r,t)");
  this.dims = dimensions;
  this.bts = basic_timestep;
  this.time = 0;
  this.hasPlaceCollision = false;

  this.cpSpace = new cp.Space();
  this.cpSpace.gravity = new cp.v(0, -gravity);

  this.objects = {};
  this.blockers = {};
  this.constraints = {}; // These aren't implemented yet

  this.goalCond = null;
  this.winCallback = null;
  this._collisionEvents = [];
  this.ssBegin = _emptyObjectHandler;
  this.ssPre = _emptyObjectHandler;
  this.ssPost = _emptyObjectHandler;
  this.ssEnd = _emptyObjectHandler;
  this.sgBegin = _emptyObjectHandler;
  this.sgEnd = _emptyObjectHandler;

  // Collision handlers to deal with goal objects
  me = this;
  this.cpSpace.addCollisionHandler(COLTYPE_SOLID, COLTYPE_SOLID,
    function(arb, space) {
      return ssbeg(arb, space, me);
    },
    function(arb, space) {
      return sspre(arb, space, me);
    },
    function(arb, space) {
      return sspost(arb, space, me);
    },
    function(arb, space) {
      return ssend(arb, space, me);
    });
  this.cpSpace.addCollisionHandler(COLTYPE_PLACED, COLTYPE_SOLID,
    function (arb, space) {
      return ssbeg(arb, space, me);
    },
    function (arb, space) {
      return sspre(arb, space, me);
    },
    function (arb, space) {
      return sspost(arb, space, me);
    },
    function (arb, space) {
      return ssend(arb, space, me);
    });
  this.cpSpace.addCollisionHandler(COLTYPE_SOLID, COLTYPE_SENSOR,
    function(arb, space) {
      return sgbeg(arb, space, me);
    },
    null,
    null,
    function(arb, space) {
      return sgend(arb, space, me);
    });
  this.cpSpace.addCollisionHandler(COLTYPE_PLACED, COLTYPE_SENSOR,
    function(arb, space) {
      return sgbeg(arb, space, me);
    },
    null,
    null,
    function(arb, space) {
      return sgend(arb, space, me);
    });

  // Set up the bounding edges
  if (closed_ends[0]) {
    this.addBox("_LeftWall", [-1, -1, 1, this.dims[1] + 1], this.def_col, 0);
  }
  if (closed_ends[1]) {
    this.addBox("_BottomWall", [-1, -1, this.dims[0] + 1, 1], this.def_col, 0);
  }
  if (closed_ends[2]) {
    this.addBox("_RightWall", [this.dims[0] - 1, -1, this.dims[0] + 1, this.dims[1] + 1], this.def_col, 0);
  }
  if (closed_ends[3]) {
    this.addBox("_TopWall", [-1, this.dims[1] - 1, this.dims[0] + 1, this.dims[1] + 1], this.def_col, 0);
  }

};

PGWorld.prototype.step = function(t) {
  var nsteps = Math.floor(t / this.bts);
  var remtime = this.bts % t;
  this.time += t;

  for (var i = 0; i < nsteps; i++) {
    this.cpSpace.step(this.bts);
    if (this.checkEnd() && this.winCallback !== null) {
      this.winCallback();
    };
  }
  this.cpSpace.step(remtime);
  if (this.checkEnd() && this.winCallback !== null) {
    this.winCallback();
  };
};

// To translate to a canvas
PGWorld.prototype._invert = function(pt) {
  return [pt[0], this.dims[1] - pt[1]];
};

PGWorld.prototype._yinvert = function(y) {
  return this.dims[1] - y;
};


// Helper function that gets reused
PGWorld.prototype._drawSeg = function(ctx, p1, p2, r, color) {
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(p1[0], p1[1], r, 0, 2 * Math.PI);
  ctx.fill();
  ctx.lineWidth = r * 2;
  ctx.beginPath();
  ctx.moveTo(p1[0], p1[1]);
  ctx.lineTo(p2[0], p2[1]);
  ctx.stroke();
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(p2[0], p2[1], r, 0, 2 * Math.PI);
  ctx.fill();
};

PGWorld.prototype._drawPoly = function(ctx, vtx, color) {
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.beginPath();
  ctx.moveTo(vtx[0][0], this._yinvert(vtx[0][1]));
  for (var i = 1; i < vtx.length; i++) {
    ctx.lineTo(vtx[i][0], this._yinvert(vtx[i][1]));
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
};

PGWorld.prototype.draw = function(canvas) {
  var ctx = canvas.getContext('2d');

  var oldcompop = ctx.globalCompositeOperation;
  ctx.globalCompositeOperation = 'source-over';

  ctx.fillStyle = this.bk_col;
  ctx.fillRect(0, 0, this.dims[0], this.dims[1]);

  for (var bnm in this.blockers) {
    var b = this.blockers[bnm];
    var vtxs = b.getVertices();
    ctx.fillStyle = b.color;
    ctx.beginPath();
    ctx.moveTo(vtxs[0][0], this._invert(vtxs[0])[1]);
    for (var i = 1; i < vtxs.length; i++) {
      var v = this._invert(vtxs[i]);
      ctx.lineTo(v[0], v[1]);
    }
    ctx.closePath();
    ctx.fill();
  }

  for (var onm in this.objects) {
    var o = this.objects[onm];
    if (o.type === 'Poly') {
      var vtxs = o.getVertices();
      ctx.fillStyle = o.color;
      ctx.beginPath();
      ctx.moveTo(vtxs[0][0], this._invert(vtxs[0])[1]);
      for (var i = 1; i < vtxs.length; i++) {
        var v = this._invert(vtxs[i]);
        ctx.lineTo(v[0], v[1]);
      }
      ctx.closePath();
      ctx.fill();
    } else if (o.type === 'Ball') {
      var pos = this._invert(o.getPos());
      var rad = o.getRadius();
      ctx.fillStyle = o.color;
      ctx.beginPath();
      ctx.arc(pos[0], pos[1], rad, 0, 2 * Math.PI);
      ctx.fill();
    } else if (o.type === 'Segment') {
      var pts = o.getPoints();
      pts = [this._invert(pts[0]), this._invert(pts[1])];
      this._drawSeg(ctx, pts[0], pts[1], o.r, o.color);
    } else if (o.type === 'Container') {
      var polys = o.getPolys();
      for (var i = 0; i < polys.length; i++) {
        this._drawPoly(ctx, polys[i], o.color);
      }
    } else if (o.type === 'Compound') {
      var polys = o.getPolys();
      for (var i = 0; i < polys.length; i++) {
        this._drawPoly(ctx, polys[i], o.color);
      }
    } else {
      console.log("Error: invalid object type for drawing");
    }
  }
};


PGWorld.prototype.checkEnd = function() {
  if (this.goalCond === null) return false;
  return this.goalCond.isWon();
};

PGWorld.prototype.getObject = function(name) {
  assert(name in this.objects, "No object by that name: " + name);
  return this.objects[name];
};

PGWorld.prototype.getGravity = function() {
  return -this.cpSpace.gravity.y;
};

PGWorld.prototype.addPoly = function(name, vertices, color, density, elasticity, friction) {
  assert(!(name in this.objects), "Name already taken: " + name);

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var thisObj = new PGPoly(name, this.cpSpace, vertices, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addBox = function(name, bounds, color, density, elastiticy, friction) {
  assert(!(name in this.objects), "Name already taken");
  assert(bounds.length === 4, "Need four numbers for bounds [l,b,r,t]");

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var l = bounds[0],
    b = bounds[1],
    r = bounds[2],
    t = bounds[3];
  var vertices = [
    [l, b],
    [l, t],
    [r, t],
    [r, b]
  ];

  var thisObj = new PGPoly(name, this.cpSpace, vertices, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addBall = function(name, position, radius, color, density, elasticity, friction) {
  assert(!(name in this.objects), "Name already taken");

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var thisObj = new PGBall(name, this.cpSpace, position, radius, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addSegment = function(name, p1, p2, width, color, density, elasticity, friction) {
  assert(!(name in this.objects), "Name already taken");

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var thisObj = new PGSeg(name, this.cpSpace, p1, p2, width, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addContainer = function(name, ptlist, width, color, density, elasticity, friction) {
  assert(!(name in this.objects), "Name already taken");

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var thisObj = new PGContainer(name, this.cpSpace, ptlist, width, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addCompound = function(name, polys, color, density, elasticity, friction) {
  assert(!(name in this.objects), "Name already taken");

  var density = typeof density !== 'undefined' ? density : this.def_density;
  var elasticity = typeof elasticity !== 'undefined' ? elasticity : this.def_elasticity;
  var friction = typeof friction !== 'undefined' ? friction : this.def_friction;

  var thisObj = new PGCompound(name, this.cpSpace, polys, density, elasticity, friction, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addPolyGoal = function(name, vertices, color) {
  assert(!(name in this.objects), "Name already taken");

  var thisObj = newPGGoal(name, this.cpSpace, vertices, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addBoxGoal = function(name, bounds, color) {
  assert(!(name in this.objects), "Name already taken");

  var l = bounds[0],
    b = bounds[1],
    r = bounds[2],
    t = bounds[3];
  var vertices = [
    [l, b],
    [l, t],
    [r, t],
    [r, b]
  ];

  var thisObj = newPGGoal(name, this.cpSpace, vertices, color);
  this.objects[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addPlacedPoly = function(name, vertices, color, density, elasticity, friction) {
  var thisObj = this.addPoly(name, vertices, color, density, elasticity, friction);
  thisObj.cpShape.setCollisionType(COLTYPE_PLACED);
  return thisObj;
};

PGWorld.prototype.addPlacedCompound = function(name, polys, color, density, elasticity, friction) {
  var thisObj = this.addCompound(name, polys, color, density, elasticity, friction);
  for (var i = 0; i < thisObj.cpShapes.length; i++) {
    thisObj.cpShapes[i].setCollisionType(COLTYPE_PLACED);
  }
  return thisObj;
};

PGWorld.prototype.addBlock = function(name, bounds, color) {
  assert(!(name in this.blockers), "Name already taken");
  assert(bounds.length === 4, "Need four numbers for bounds [l,b,r,t]");

  var l = bounds[0],
    b = bounds[1],
    r = bounds[2],
    t = bounds[3];
  var vertices = [
    [l, b],
    [l, t],
    [r, t],
    [r, b]
  ];

  var thisObj = new PGBlocker(name, this.cpSpace, vertices, color);
  this.blockers[name] = thisObj;
  return thisObj;
};

PGWorld.prototype.addPolyBlock = function(name, vertices, color) {
  assert(!(name in this.blockers), "Name already taken");

  var thisObj = new PGBlocker(name, this.cpSpace, vertices, color);
  this.blockers[name] = thisObj;
  return thisObj;
};

// Functions for handling callbacks in a nice way

PGWorld.prototype.setSolidCollisionPre = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.ssPre = fnc;
};

PGWorld.prototype.setSolidCollisionPost = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.ssPost = fnc;
};

PGWorld.prototype.setSolidCollisionBegin = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.ssBegin = fnc;
};

PGWorld.prototype.setSolidCollisionEnd = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.ssEnd = fnc;
};

PGWorld.prototype.setGoalCollisionBegin = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.sgBegin = fnc;
};

PGWorld.prototype.setGoalCollisionEnd = function(fnc) {
  var fnc = typeof(fnc) !== 'undefined' ? fnc : _emptyObjectHandler;
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.sgEnd = fnc;
};

PGWorld.prototype._solidSolidPre = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o1 = me.getObject(onms[0]);
  var o2 = me.getObject(onms[1]);
  me.ssPre(o1, o2);
};

PGWorld.prototype._solidSolidPost = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o1 = me.getObject(onms[0]);
  var o2 = me.getObject(onms[1]);
  me.ssPost(o1, o2);
};

PGWorld.prototype._solidSolidBegin = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o1 = me.getObject(onms[0]);
  var o2 = me.getObject(onms[1]);
  if (!(o1.isStatic() && o2.isStatic())) me._collisionEvents.push([onms[0], onms[1], "begin", me.time]);
  me.ssBegin(o1, o2);
};

PGWorld.prototype._solidSolidEnd = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o1 = me.getObject(onms[0]);
  var o2 = me.getObject(onms[1]);
  if (!(o1.isStatic() && o2.isStatic())) me._collisionEvents.push([onms[0], onms[1], "end", me.time]);
  me.ssEnd(o1, o2);
};

PGWorld.prototype._solidGoalBegin = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o = me.getObject(onms[0]);
  var g = me.getObject(onms[1]);
  me.sgBegin(o, g);
};

PGWorld.prototype._solidGoalEnd = function(arb, space, me) {
  var onms = resolveArbiter(arb, space);
  var o = me.getObject(onms[0]);
  var g = me.getObject(onms[1]);
  me.sgEnd(o, g);
};

// Attaching success conditions

PGWorld.prototype.callbackOnWin = function(fnc) {
  assert(isFunction(fnc), "Must pass legal function to callback setter");
  this.winCallback = fnc;
};

PGWorld.prototype.attachAnyInGoal = function(goalname, duration, exclusions) {
  var me = this;
  this.goalCond = new PGCond_AnyInGoal(goalname, duration, me, exclusions);
  this.goalCond.attachHooks();
};

PGWorld.prototype.attachSpecificInGoal = function(goalname, objname, duration) {
  var me = this;
  this.goalCond = new PGCond_SpecificInGoal(goalname, objname, duration, me);
  this.goalCond.attachHooks();
};

PGWorld.prototype.attachAnyTouch = function(objname, duration) {
  var me = this;
  this.goalCond = new PGCond_AnyTouch(objname, duration, me);
  this.goalCond.attachHooks();
};

PGWorld.prototype.attachSpecificTouch = function(obj1, obj2, duration) {
  var me = this;
  this.goalCond = new PGCond_SpecificTouch(obj1, obj2, duration, me);
  this.goalCond.attachHooks();
};

PGWorld.prototype.checkFinishers = function() {
  return (this.goalCond !== null && this.winCallback !== null);
};

// Checking collision events
PGWorld.prototype.resetCollisions = function() {
  this._collisionEvents = [];
};

PGWorld.prototype.getCollisionEvents = function() {
  return this._collisionEvents;
};

// Checking for legal placement of an object
PGWorld.prototype._hitOnPlacementCollision = function(me) {
  me.hasPlaceCollision = true;
  return false;
};

PGWorld.prototype.checkCollision = function(pos, verts) {

  // Translate the vertices to the position & flatten them
  var fverts = [];
  for (var i = 0; i < verts.length; i++) {
    fverts.push(pos[0] + verts[i][0], pos[1] + verts[i][1]);
  }

  // Make a new chipmunk poly object with those vertices
  var tmpBody = new cp.Body(1, 1);
  var placeShape = new cp.PolyShape(tmpBody, fverts, cp.vzero);
  placeShape.setCollisionType(COLTYPE_CHECKER);
  placeShape.sensor = true;

  // Add the shape, take check for collisions & set hit if found
  this.hasPlaceCollision = false;
  me = this;
  this.cpSpace.shapeQuery(placeShape, function() {
    me._hitOnPlacementCollision(me);
  });
  // Note: may want to do further checking for collision types later

  var ret = this.hasPlaceCollision;
  this.hasPlaceCollision = false;
  return ret;

};

// Output the world to a JSON file
PGWorld.prototype.toDict = function() {
  var wdict = {};
  wdict.dims = this.dims;
  wdict.bts = this.bts;
  wdict.gravity = this.getGravity();
  wdict.defaults = {
    density: this.def_density,
    friction: this.def_friction,
    elasticity: this.def_elasticity,
    color: this.def_col,
    bk_color: this.bk_col
  };

  // Save the objects
  wdict.objects = {};
  for (var nm in this.objects) {
    var o = this.objects[nm];
    var attrs = {
      type: o.type,
      color: o.color,
      density: o.density,
      friction: o.friction,
      elasticity: o.elasticity
    };

    if (o.type === 'Poly') {
      attrs.vertices = o.getVertices();
    } else if (o.type === 'Ball') {
      attrs.position = o.getPos();
      attrs.radius = o.getRadius();
    } else if (o.type === 'Segment') {
      var pts = o.getPoints();
      attrs.p1 = pts[0];
      attrs.p2 = pts[1];
      attrs.width = o.r * 2;
    } else if (o.type === 'Container') {
      attrs.points = o.getVertices();
      attrs.width = o.r * 2;
    } else if (o.type === 'Goal') {
      attrs.vertices = o.getVertices();
    } else if (o.type === 'Compound') {
      attrs.polys = o.getPolys();
    } else {
      throw new AssertException("Illegal object type encountered: " + o.type);
    }
    wdict.objects[nm] = attrs;
  }

  // Blocking objects
  wdict.blocks = {};
  for (var nm in this.blockers) {
    var b = this.blockers[nm];
    var attrs = {
      color: b.color,
      vertices: b.getVertices()
    }
    wdict.blocks[nm] = attrs;
  }

  // Constraints not yet added
  wdict.constraints = {};

  if (this.goalCond === null) {
    wdict.gcond = null;
  } else {
    if (this.goalCond.type === "AnyInGoal") {
      wdict.gcond = {
        type: "AnyInGoal",
        goal: this.goalCond.goal,
        obj: "-",
        exclusions: this.goalCond.excl,
        duration: this.goalCond.dur
      };
    } else if (this.goalCond.type === "SpecificInGoal") {
      wdict.gcond = {
        type: "SpecificInGoal",
        goal: this.goalCond.goal,
        obj: this.goalCond.obj,
        duration: this.goalCond.dur
      };
    } else if (this.goalCond.type === "AnyTouch") {
      wdict.gcond = {
        type: "AnyTouch",
        goal: this.goalCond.goal,
        obj: "-",
        duration: this.goalCond.dur
      };
    } else if (this.goalCond.type === "SpecificTouch") {
      wdict.gcond = {
        type: "SpecificTouch",
        obj: this.goalCond.o1,
        goal: this.goalCond.o2,
        duration: this.goalCond.dur
      }
    } else {
      throw new AssertException("Illegal goal condition type encountered: " + this.goalCond.type);
    }
  }

  return wdict;
};

var loadFromDict = function(worldDict) {
  var d = worldDict;
  var pgw = new PGWorld(d.dims, d.gravity, [false, false, false, false], d.bts,
    d.defaults.density, d.defaults.elasticity, d.defaults.friction,
    d.defaults.bk_col, d.defaults.color);

  for (var nm in d.objects) {
    var o = d.objects[nm];
    if (o.type === 'Poly') {
      pgw.addPoly(nm, o.vertices, o.color, o.density, o.elasticity, o.friction);
    } else if (o.type === 'Ball') {
      pgw.addBall(nm, o.position, o.radius, o.color, o.density, o.elasticity, o.friction);
    } else if (o.type === 'Segment') {
      pgw.addSegment(nm, o.p1, o.p2, o.width, o.color, o.density, o.elasticity, o.friction);
    } else if (o.type === 'Container') {
      pgw.addContainer(nm, o.points, o.width, o.color, o.density, o.elasticity, o.friction);
    } else if (o.type === 'Goal') {
      pgw.addPolyGoal(nm, o.vertices, o.color);
    } else if (o.type === 'Compound') {
      pgw.addCompound(nm, o.polys, o.color, o.density, o.elasticity, o.friction);
    } else {
      throw new AssertException("Illegal object type encountered: " + o.type);
    }
  }

  for (var nm in d.blocks) {
    var b = d.blocks[nm];
    pgw.addPolyBlock(nm, b.vertices, b.color);
  }

  // TO DO: Add onstraints

  if (d.gcond !== null) {
    var g = d.gcond;
    if (g.type === 'AnyInGoal') {
      pgw.attachAnyInGoal(g.goal, g.duration, g.exclusions);
    } else if (g.type === 'SpecificInGoal') {
      pgw.attachSpecificInGoal(g.goal, g.obj, g.duration);
    } else if (g.type === "AnyTouch") {
      pgw.attachAnyTouch(g.goal, g.duration);
    } else if (g.type === "SpecificTouch") {
      pgw.attachSpecificTouch(g.goal, g.obj, g.duration);
    } else {
      throw new AssertException("Illegal goal condition type encountered: " + g.type);
    }
  }

  return pgw;
};

module.exports = {
  World: PGWorld,
  assert: assert,
  isFunction: isFunction,
  loadFromDict: loadFromDict,
  coltype_solid: COLTYPE_SOLID,
  coltype_sensor: COLTYPE_SENSOR,
  coltype_placed: COLTYPE_PLACED,
  coltype_blocked: COLTYPE_BLOCKED,
  coltype_checker: COLTYPE_CHECKER
};
