import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import SpyAssignedEvent, VoteSubmittedEvent

CATEGORIES = {
    "Locations": ["Hospital", "Submarine", "Space Station", "School", "Bank", "Casino", "Police Station", "Circus", "Pirate Ship", "Military Base"],
    "Food": ["Pizza", "Sushi", "Burger", "Pasta", "Salad", "Steak", "Tacos"],
    "Animals": ["Lion", "Elephant", "Penguin", "Shark", "Eagle", "Tiger", "Bear"],
    "Countries": ["Japan", "Brazil", "Canada", "France", "Australia", "Egypt", "Italy"],
    "Cities": ["New York", "Tokyo", "London", "Paris", "Cairo", "Dubai", "Rome"],
    "Professions": ["Doctor", "Teacher", "Engineer", "Chef", "Pilot", "Lawyer", "Scientist"],
    "Movies": ["The Godfather", "Titanic", "Avatar", "Star Wars", "Jurassic Park", "The Matrix", "Inception"],
    "TV Shows": ["Breaking Bad", "Game of Thrones", "Friends", "The Office", "Stranger Things", "The Simpsons"],
    "Brands": ["Apple", "Nike", "Coca-Cola", "Google", "Samsung", "Amazon", "Microsoft"],
    "Cars": ["Tesla", "Toyota", "Ford", "BMW", "Ferrari", "Porsche", "Honda"],
    "Sports": ["Soccer", "Basketball", "Tennis", "Swimming", "Cricket", "Volleyball", "Baseball"],
    "Video Games": ["Minecraft", "Tetris", "Super Mario", "GTA V", "Zelda", "Fortnite", "Call of Duty"],
    "Musical Instruments": ["Piano", "Guitar", "Violin", "Drums", "Flute", "Saxophone", "Trumpet"],
    "Technology": ["Smartphone", "Laptop", "Smartwatch", "Drone", "VR Headset", "Tablet", "Camera"],
    "Historical Figures": ["Albert Einstein", "Cleopatra", "Leonardo da Vinci", "Abraham Lincoln", "Marie Curie"],
    "Fruits": ["Apple", "Banana", "Orange", "Strawberry", "Mango", "Grapes", "Watermelon"],
    "Vegetables": ["Carrot", "Broccoli", "Tomato", "Spinach", "Potato", "Cucumber", "Onion"],
    "Drinks": ["Coffee", "Tea", "Water", "Juice", "Soda", "Milk", "Lemonade"],
    "Objects": ["Chair", "Table", "Lamp", "Clock", "Book", "Pen", "Cup"],
    "Jobs": ["Actor", "Artist", "Writer", "Musician", "Dancer", "Photographer", "Designer"],
    "School Items": ["Pencil", "Notebook", "Eraser", "Backpack", "Ruler", "Marker", "Calculator"],
    "Space": ["Moon", "Sun", "Mars", "Black Hole", "Galaxy", "Asteroid", "Comet"],
    "Egyptian Culture": ["Pyramids", "Sphinx", "Nile River", "Pharaoh", "Papyrus", "Mummy", "Koshary"]
}

class SpyPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.spy"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Spy",
            "category": "SOCIAL_DEDUCTION",
            "min_players": 3,
            "max_players": 12,
            "has_turns": False,
            "categories": list(CATEGORIES.keys())
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        spies_count = config.get("spies_count", 1)
        if not isinstance(spies_count, int) or spies_count < 1: return False
        
        # Validate category if passed
        category = config.get("category")
        if category and category not in CATEGORIES and category != "Custom Categories":
            return False
            
        # Validate custom categories if Custom Categories is selected
        if category == "Custom Categories":
            custom_locations = config.get("custom_locations")
            if not isinstance(custom_locations, list) or len(custom_locations) < 2:
                return False
                
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 3: return
        
        # Determine spy
        num_spies = 1 # Simple MVP
        spies = random.sample(players, num_spies)
        
        # For MVP, we randomly select a category if we can't access config.
        # In a real scenario, the match configuration would dictate this.
        category_name = random.choice(list(CATEGORIES.keys()))
        location_list = CATEGORIES[category_name]
        location = random.choice(location_list)
        
        state = {
            "players": players,
            "spies": spies,
            "category": category_name,
            "location": location,
            "votes": {},
            "winner_team": None # 'SPIES' or 'AGENTS'
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        EventDispatcher.publish(SpyAssignedEvent(match_id=match_id, spy_ids=spies))

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        if action.get("type") != "SUBMIT_VOTE":
            return False
            
        target_id = action.get("target_id")
        if not target_id: return False
        
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        state["votes"][player_id] = target_id
        EventDispatcher.publish(VoteSubmittedEvent(match_id=match_id, voter_id=player_id, target_id=target_id))
        
        # Check if everyone voted
        if len(state["votes"]) == len(state["players"]):
            # Count votes
            vote_counts = {}
            for target in state["votes"].values():
                vote_counts[target] = vote_counts.get(target, 0) + 1
                
            # Highest voted
            highest_voted = max(vote_counts, key=vote_counts.get)
            
            if highest_voted in state["spies"]:
                state["winner_team"] = "AGENTS"
            else:
                state["winner_team"] = "SPIES"
                
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        return True

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner_team"]: return []
        
        if state["winner_team"] == "SPIES":
            return state["spies"]
        else:
            return [p for p in state["players"] if p not in state["spies"]]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")
