from pyGameWorld import PGWorld, ToolPicker
from pyGameWorld.viewer import demonstrateTPPlacement
import json
import pygame as pg

# Make the basic world
pgw = PGWorld(dimensions=(600,600), gravity=200)
# Name, [left, bottom, right, top], color, density (0 is static)
pgw.addBox('Table', [0,0,300,200],(0,0,0),0)
# Name, points (counter-clockwise), width, color, density
pgw.addContainer('Goal', [[330,100],[330,5],[375,5],[375,100]], 10, (0,255,0), (0,0,0), 0)
# Name, position of center, radius, color, (density is 1 by default)
pgw.addBall('Ball',[100,215],15,(0,0,255))

# Sets up the condition that "Ball" must go into "Goal" and stay there for 2 seconds
pgw.attachSpecificInGoal("Goal","Ball",2.)
pgw_dict = pgw.toDict()

'''
# Save to a file
# Can reload with loadFromDict function in pyGameWorld

with open('basic_trial.json','w') as jfl:
    json.dump(pgw_dict, jfl)
'''

tools = {
    "obj1" : [[[-30,-15],[-30,15],[30,15],[0,-15]]],
    "obj2" : [[[-20,0],[0,20],[20,0],[0,-20]]],
    "obj3" : [[[-40,-5],[-40,5],[40,5],[40,-5]]]
    }

# Turn this into a toolpicker game
# Takes in the "toDict" translation of a world and tool dictionary
tp = ToolPicker(
    {'world': pgw_dict,
     'tools': tools}
)

'''
# Save to a file
# Can reload with loadToolPicker in pyGameWorld

with open('basic_tp.json','w') as tpfl:
    json.dump({'world':pgw_dict, 'tools':tools}, tpfl)
'''

# Find the path of objects over 2s
# Comes out as a dict with the moveable object names
# (PLACED for the placed tool) with a list of positions over time each
path_dict, success, time_to_success = tp.observePlacementPath(toolname="obj1",position=(90,400),maxtime=20.)
print("Action was successful? ", success)

# View that placement
demonstrateTPPlacement(tp, 'obj1', (90, 400))

# Load level in from json file
# For levels used in experiment, check out Level_Definitions/
json_dir = "./Trials/Original/"
tnm = "Basic"

with open(json_dir+tnm+'.json','r') as f:
  btr = json.load(f)

tp = ToolPicker(btr)

# View that placement
demonstrateTPPlacement(tp, 'obj1', (90, 400))