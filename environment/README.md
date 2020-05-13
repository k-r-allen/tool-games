Python package to run the GameWorld (for interfacing with RL packages, etc)

To install, make sure you have the following packages:

* numpy
* scipy
* pymunk (>= 5.0)
* execjs (installed by `pip install PyExecJS`)

You will also need node.js

The following package is not required, but you probably want it for visualization:

* pygame

Then just run the following code in this directory:

> python setup.py build

In the basic pyGameWorld package, the main draw is the ToolPicker, which lets you take in ToolPicker json files to play the levels more easily. For examples on how to use the ToolPicker object, including creating new worlds, take a look at `make_basic_world.py`


