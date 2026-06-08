import json
import os
import sys

# When running as a PyInstaller .exe, __file__ points inside the temp extraction
# dir which is deleted on exit. Use sys.executable to find the real .exe location.
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(_base, "data.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"income": 0, "commitments": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fmt(amount):
    return f"RM {amount:,.2f}"
