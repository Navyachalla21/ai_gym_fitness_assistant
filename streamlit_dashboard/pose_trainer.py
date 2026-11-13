"""Live AI trainer that runs in the user's own browser (laptop webcam or phone camera)."""
import os

import streamlit.components.v1 as components

_component = components.declare_component(
    "pose_trainer", path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_component"))


def pose_trainer(key: str = "live_trainer"):
    """Shows the camera trainer. Returns a dict when the user presses 'Finish and analyze', else None."""
    return _component(key=key, default=None)
