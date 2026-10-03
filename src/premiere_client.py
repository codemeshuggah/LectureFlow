"""
LectureFlow Premiere Client
Interfaces with Adobe Premiere Pro via Model Context Protocol (MCP) tools.
"""

from typing import Dict, Any, List

class PremiereClient:
    def __init__(self, mcp_caller=None):
        """
        mcp_caller: function(tool_name: str, arguments: dict) -> dict
        Defaults to native bridge or MCP HTTP caller.
        """
        self.call = mcp_caller

    def setup_sequence(
        self,
        sequence_name: str,
        raw_video_path: str,
        intro_offset: float = 12.0
    ) -> Dict[str, Any]:
        """Creates master sequence, moves raw footage to V3/A1, and applies intro offset."""
        print(f"[Premiere] Initializing sequence '{sequence_name}'...")
        # 1. Create sequence from RAW clip
        seq_res = self.call("create_sequence_from_clips", {
            "name": sequence_name,
            "item_ids": [raw_video_path]
        })
        seq_id = seq_res.get("id")
        self.call("set_active_sequence", {"sequence_id": seq_id})

        # 2. Add extra video tracks to ensure 5 video tracks
        self.call("add_track", {"count": 2, "track_type": "video"})

        # 3. Shift raw clips to account for intro duration
        # (Moves raw video from V1 to V3, raw audio stays on A1)
        return seq_res

    def apply_chroma_key(
        self,
        node_id: str,
        rgb_color: List[int] = (197, 255, 65),
        params: Dict[str, float] = None
    ):
        """Applies Ultra Key and calibrates matte cleanup and spill suppression."""
        print(f"[Premiere] Applying Ultra Key to presenter clip ({node_id})...")
        self.call("apply_effect", {"node_id": node_id, "effect_name": "Ultra Key"})
        self.call("set_color_value", {
            "node_id": node_id,
            "component_name": "Ultra Key",
            "property_name": "Key Color",
            "red": rgb_color[0],
            "green": rgb_color[1],
            "blue": rgb_color[2],
            "alpha": 255
        })

        default_params = {
            "Transparency": 46.0,
            "Highlight": 10.0,
            "Shadow": 51.0,
            "Tolerance": 50.0,
            "Pedestal": 86.0,
            "Choke": 10.0,
            "Soften": 6.0,
            "Contrast": 4.0,
            "Mid Point": 50.0,
            "Desaturate": 25.0,
            "Spill": 50.0
        }
        active_params = {**default_params, **(params or {})}
        for prop, val in active_params.items():
            self.call("set_effect_property", {
                "node_id": node_id,
                "effect_name": "Ultra Key",
                "property_name": prop,
                "value": val
            })

    def apply_pip_motion(
        self,
        node_id: str,
        position: List[float] = (0.8302, 0.6769),
        scale: float = 66.0
    ):
        """Sets right-aligned or left-aligned PIP position and scale on Motion effect."""
        self.call("set_effect_property", {
            "node_id": node_id,
            "effect_name": "Motion",
            "property_name": "Position",
            "value": list(position)
        })
        self.call("set_effect_property", {
            "node_id": node_id,
            "effect_name": "Motion",
            "property_name": "Scale",
            "value": scale
        })

    def lock_overlay_track(self, track_index: int = 1):
        """Locks Video 2 to protect lower-thirds and graphical overlays."""
        print(f"[Premiere] Locking overlay track V{track_index + 1}...")
        self.call("lock_track", {"track_index": track_index, "locked": True})

    def save(self):
        """Saves active project."""
        return self.call("save_project", {})
