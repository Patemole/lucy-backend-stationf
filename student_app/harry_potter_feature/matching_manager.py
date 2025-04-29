# matching_manager.py
"""
lucy – harry potter housing matcher (upenn edition)
-----------------------------------------------
call match_houses({...}) with a dict where
    key   = attribute name
    value = 1 (swipe right) or 0 (swipe left)
returns an ordered list of tuples: [(house, score%), ...]
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. reference attributes
# ---------------------------------------------------------------------------

ATTRIBUTES: List[str] = [
    "dining_in_house",
    "air_conditioning",
    "suite_style",
    "traditions_social",
    "quiet_academic",
    "budget_friendly",
    "close_to_engineering",
    "historic_vibe",
    "modern_facilities",
    "private_bath",
    "faculty_involvement",
    "theme_floor",
    "small_community",
    "green_space",
    "skyline_views",
    "in_house_fitness",
    "creative_spaces",
    "sink_in_room",
    "easy_laundry",
    "late_night_food",
    "first_year_only",
    "lounge_capacity",
    "natural_light",
    "active_house_programs",
]

# uniform weight (tune later if needed)
WEIGHTS: Dict[str, float] = {attr: 1.0 for attr in ATTRIBUTES}

# ---------------------------------------------------------------------------
# 2. per-house profiles
# ---------------------------------------------------------------------------

hill = {
    "dining_in_house": 2,
    "air_conditioning": 2,
    "suite_style": 0,
    "traditions_social": 1,
    "quiet_academic": 1,
    "budget_friendly": 1,
    "close_to_engineering": 2,
    "historic_vibe": 0,
    "modern_facilities": 2,
    "private_bath": 0,
    "faculty_involvement": 1,
    "theme_floor": 0,
    "small_community": 2,
    "green_space": 1,
    "skyline_views": 0,
    "in_house_fitness": 2,
    "creative_spaces": 1,
    "sink_in_room": 0,
    "easy_laundry": 2,
    "late_night_food": 1,
    "first_year_only": 2,
    "lounge_capacity": 2,
    "natural_light": 1,
    "active_house_programs": 2,
}

kings_court_english = {
    "dining_in_house": 2,
    "air_conditioning": 0,
    "suite_style": 0,
    "traditions_social": 0,
    "quiet_academic": 2,
    "budget_friendly": 1,
    "close_to_engineering": 2,
    "historic_vibe": 0,
    "modern_facilities": 1,
    "private_bath": 0,
    "faculty_involvement": 2,
    "theme_floor": 2,
    "small_community": 1,
    "green_space": 1,
    "skyline_views": 0,
    "in_house_fitness": 1,
    "creative_spaces": 1,
    "sink_in_room": 2,
    "easy_laundry": 1,
    "late_night_food": 0,
    "first_year_only": 2,
    "lounge_capacity": 1,
    "natural_light": 1,
    "active_house_programs": 2,
}

lauder = {
    "dining_in_house": 2,
    "air_conditioning": 2,
    "suite_style": 2,
    "traditions_social": 1,
    "quiet_academic": 1,
    "budget_friendly": 0,
    "close_to_engineering": 1,
    "historic_vibe": 0,
    "modern_facilities": 2,
    "private_bath": 2,
    "faculty_involvement": 2,
    "theme_floor": 1,
    "small_community": 1,
    "green_space": 2,
    "skyline_views": 1,
    "in_house_fitness": 1,
    "creative_spaces": 1,
    "sink_in_room": 0,
    "easy_laundry": 2,
    "late_night_food": 1,
    "first_year_only": 2,
    "lounge_capacity": 2,
    "natural_light": 2,
    "active_house_programs": 2,
}

gutmann = {
    "dining_in_house": 2,
    "air_conditioning": 2,
    "suite_style": 2,
    "traditions_social": 1,
    "quiet_academic": 1,
    "budget_friendly": 0,
    "close_to_engineering": 0,
    "historic_vibe": 0,
    "modern_facilities": 2,
    "private_bath": 2,
    "faculty_involvement": 2,
    "theme_floor": 1,
    "small_community": 1,
    "green_space": 2,
    "skyline_views": 2,
    "in_house_fitness": 2,
    "creative_spaces": 2,
    "sink_in_room": 0,
    "easy_laundry": 2,
    "late_night_food": 1,
    "first_year_only": 2,
    "lounge_capacity": 2,
    "natural_light": 2,
    "active_house_programs": 2,
}

fisher_base = {
    "dining_in_house": 1,
    "air_conditioning": 0,
    "suite_style": 0,
    "traditions_social": 2,
    "quiet_academic": 0,
    "budget_friendly": 2,
    "close_to_engineering": 1,
    "historic_vibe": 2,
    "modern_facilities": 0,
    "private_bath": 0,
    "faculty_involvement": 1,
    "theme_floor": 0,
    "small_community": 2,
    "green_space": 1,
    "skyline_views": 0,
    "in_house_fitness": 0,
    "creative_spaces": 0,
    "sink_in_room": 0,
    "easy_laundry": 1,
    "late_night_food": 2,
    "first_year_only": 2,
    "lounge_capacity": 2,
    "natural_light": 1,
    "active_house_programs": 2,
}

fisher = fisher_base.copy()
ware   = fisher_base.copy()
riepe  = {**fisher_base, "quiet_academic": 1}  # riepe a bit quieter

# combined matrix
HOUSE_MATRIX: Dict[str, Dict[str, int]] = {
    "hill": hill,
    "kings_court_english": kings_court_english,
    "lauder": lauder,
    "gutmann": gutmann,
    "fisher": fisher,
    "ware": ware,
    "riepe": riepe,
}

# ---------------------------------------------------------------------------
# 3. matching function
# ---------------------------------------------------------------------------

def match_houses(answers: Dict[str, int]) -> List[Tuple[str, float]]:
    """
    answers: {"air_conditioning": 1, ...}
    missing keys = question never shown → ignored in scoring
    returns list sorted by score desc, score ∈ [0,100]
    """

    answered = [a for a in answers if a in ATTRIBUTES]
    if not answered:
        raise ValueError("no valid attributes supplied")

    denom = sum(WEIGHTS[a] * 2 for a in answered)  # 2 = max strength

    ranked: List[Tuple[str, float]] = []
    for house, profile in HOUSE_MATRIX.items():
        pts = sum(
            profile.get(attr, 0) * WEIGHTS[attr] * answers[attr]
            for attr in answered
        )
        ranked.append((house, round(pts / denom * 100, 1)))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked

# ---------------------------------------------------------------------------
# 4. quick local test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_payload = {
        "air_conditioning": 1,
        "suite_style": 1,
        "private_bath": 1,
        "historic_vibe": 0,
        "budget_friendly": 0,
    }
    for h, s in match_houses(demo_payload):
        print(f"{h:<22} {s:5.1f}")

