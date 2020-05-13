DEFAULT_DENSITY = 1.
DEFAULT_ELASTICITY = 0.5
DEFAULT_FRICTION = 0.5
DEFAULT_COLOR = (0,0,0,255)
DEFAULT_GOAL_COLOR = (0, 255, 0, 255)

COLTYPE_SOLID = 100
COLTYPE_SENSOR = 101
COLTYPE_PLACED = 102
COLTYPE_BLOCKED = 103
COLTYPE_CHECKER = 104

DEFAULT_NOISE_DICT = {
    'position_static': 5.,
    'position_moving': 5.,
    'collision_direction': .2,
    'collision_elasticity': .2,
    'gravity': .2,
    'object_friction': .1,
    'object_density': .1,
    'object_elasticity': .1
}
