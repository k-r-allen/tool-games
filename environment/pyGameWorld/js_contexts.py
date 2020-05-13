
import os

modulepath = os.path.join(os.path.dirname(__file__), 'node_modules')
base_context = '''
module.paths.push('{0}')
var pg = require('PhysicsGaming')
var npg = require('NoisyPG')
function zeroIfUndef(x) {{
    return (typeof(x) === 'undefined') ? 0 : x
}}
function isntEmpty(obj) {{
  return Object.keys(obj).length > 0
}}
function applyNoise(world, noisedict) {{
    var nps = zeroIfUndef(noisedict.noise_position_static)
    var npm = zeroIfUndef(noisedict.noise_position_moving)
    var ncd = zeroIfUndef(noisedict.noise_collision_direction)
    var nce = zeroIfUndef(noisedict.noise_collision_elasticity)
    var ng = zeroIfUndef(noisedict.noise_gravity)
    var nof = zeroIfUndef(noisedict.noise_object_friction)
    var nod = zeroIfUndef(noisedict.noise_object_density)
    var noe = zeroIfUndef(noisedict.noise_object_elasticity)
    return npg.noisifyWorld(world, nps, npm, ncd, nce, ng, nof, nod, noe)
}}
function runGW(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    while (running) {{
        w.step(stepSize)
        t += stepSize
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    if (returnNewWorld) {{
        return [w.checkEnd(), t, returnWorld]
    }} else {{
        return [w.checkEnd(), t]
    }}
}}
function stepGW(worldDict, stepSize) {{
    var w = pg.loadFromDict(worldDict)
    w.step(stepSize)
    return w.toDict()
}}
function getGWPath(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [o.getPos()]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i]
            pathdict[onm].push(w.objects[onm].getPos())
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    if (returnNewWorld) {{
        return [pathdict, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, w.checkEnd(), t]
    }}
}}
function getGWPathAndRot(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [[o.getPos()], [o.getRot()]]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i]
            pathdict[onm][0].push(w.objects[onm].getPos())
            pathdict[onm][1].push(w.objects[onm].getRot())
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    if (returnNewWorld) {{
        return [pathdict, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, w.checkEnd(), t]
    }}
}}
function getGWStatePath(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [[o.getPos()[0], o.getPos()[1], o.getRot(), o.getVel()[0], o.getVel()[1]]]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i]
            pathdict[onm].push([w.objects[onm].getPos()[0], w.objects[onm].getPos()[1], w.objects[onm].getRot(), w.objects[onm].getVel()[0], w.objects[onm].getVel()[1]])
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    if (returnNewWorld) {{
        return [pathdict, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, w.checkEnd(), t]
    }}
}}
function getGWGeomPath(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    function toGeom(o) {{
        if (o.type === "Poly") {{
            return(o.getVertices())
        }} else if (o.type === "Ball") {{
            return([o.getPos(), o.getRadius()])
        }} else if (o.type === "Container" | o.type === "Compound") {{
            return (o.getPolys())
        }} else {{
            console.log("Shape type not found: ", o.type)
            return
        }}
    }}
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [[o.type, toGeom(o), o.getVel()]]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i]
            o = w.objects[onm]
            pathdict[onm].push([o.type, toGeom(o), o.getVel()])
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    if (returnNewWorld) {{
        return [pathdict, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, w.checkEnd(), t]
    }}
}}
function getGWCollisionPath(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [o.getPos()]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize;
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i];
            pathdict[onm].push(w.objects[onm].getPos())
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    collisions = w.getCollisionEvents()
    if (returnNewWorld) {{
        return [pathdict, collisions, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, collisions, w.checkEnd(), t]
    }}
}}
function getGWCollisionPathAndRot(worldDict, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = pg.loadFromDict(worldDict)
    if (typeof(noiseDict) !== 'undefined' && isntEmpty(noiseDict)) {{
        w = applyNoise(w, noiseDict)
    }}
    if (returnNewWorld){{
        var returnWorld = w.toDict()
    }}
    var running = true
    var t = 0
    var pathdict = {{}}
    var tracknames = []
    for (onm in w.objects) {{
        var o = w.objects[onm]
        if (!o.isStatic()) {{
            tracknames.push(onm)
            pathdict[onm] = [[o.getPos()], [o.getRot()]]
        }}
    }}
    while (running) {{
        w.step(stepSize)
        t += stepSize
        for (var i = 0; i < tracknames.length; i++) {{
            onm = tracknames[i]
            pathdict[onm][0].push(w.objects[onm].getPos())
            pathdict[onm][1].push(w.objects[onm].getRot())
        }}
        if (w.checkEnd() || (t >= maxtime)) {{
            running = false
        }}
    }}
    collisions = w.getCollisionEvents()
    if (returnNewWorld) {{
        return [pathdict, collisions, w.checkEnd(), t, returnWorld]
    }} else {{
        return [pathdict, collisions, w.checkEnd(), t]
    }}
}}
'''

# For the collision checker
collision_context = base_context + '''
var world = pg.loadFromDict(JSON.parse('{1}'))
world.step(.000001)
function checkSinglePlaceCollide(verts, position) {{
    return world.checkCollision(position, verts)
}}
function checkCircleCollide(position, radius) {{
    return world.checkCircleCollision(position, radius)
}}
function checkMultiPlaceCollide(tool, position) {{
    for (var i=0; i < tool.length; i++) {{
        if (checkSinglePlaceCollide(tool[i], position)) return true
    }}
    return false
}}
'''


# The full context for ToolPickers include functions to add the tools inside JS
context = collision_context + '''
function addTool(worldDict, toolverts, pos) {{
    if (typeof(toolverts) === 'undefined') return worldDict
    var ppolys = []
    for (var i = 0; i < toolverts.length; i++) {{
        var tpol = []
        for (var j = 0; j < toolverts[i].length; j++) {{
            tpol.push([toolverts[i][j][0] + pos[0], toolverts[i][j][1] + pos[1]])
        }}
        ppolys.push(tpol)
    }}
    worldDict.objects["PLACED"] = {{
        type: "Compound",
        color: "blue",
        density: 1,
        polys: ppolys
    }}
    return worldDict
}}
function addBall(worldDict, pos, rad) {{
    if (typeof(pos) === 'undefined') return worldDict
    worldDict.objects["PLACED"] = {{
        type: "Ball",
        color: "blue",
        density: 1,
        position: pos,
        radius: rad
    }}
    return worldDict
}}
function runGWPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return runGW(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWPathPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWPath(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWPathAndRotPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWPathAndRot(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWStatePathPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWStatePath(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWCollisionPathPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWCollisionPath(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWCollisionPathAndRotPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWCollisionPathAndRot(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
function getGWGeomPathPlacement(worldDict, toolverts, pos, maxtime, stepSize, noiseDict, returnNewWorld) {{
    var w = addTool(worldDict, toolverts, pos)
    return getGWGeomPath(w, maxtime, stepSize, noiseDict, returnNewWorld)
}}
'''
