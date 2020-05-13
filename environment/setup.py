#!/usr/bin/env python
import distutils
import distutils.command.install_data
from distutils.core import setup
import os

pkgs = ['pyGameWorld']
try:
      import pygame
      pkgs.append('pyGameWorld.viewer')
except:
      print("Warning: requires 'pygame' package to run viewer; viewer not installed")

print(pkgs)
setup(name='pyGameWorld',
      version='1.0',
      description="Code for running the physics GameWorld through python",
      author="Kevin A Smith",
      author_email="k2smith@mit.edu",
      packages=pkgs,
      requires=['numpy', 'scipy','pymunk(>=5.0)','execjs']
      )
