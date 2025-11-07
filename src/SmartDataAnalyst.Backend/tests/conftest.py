import sys
import os
import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

sys.path.append(str(PROJECT_ROOT))

print(f"Added to sys.path: {PROJECT_ROOT}")