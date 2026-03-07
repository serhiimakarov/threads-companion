#!/usr/bin/env python3
import sys
import os

# Add the current directory to the python path
sys.path.append(os.getcwd())

from src.cli import main

if __name__ == "__main__":
    main()
