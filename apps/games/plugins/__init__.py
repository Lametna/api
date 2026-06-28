# Registry of all Wave 1 Games
from .number_guessing.plugin import NumberGuessingPlugin
from .spy.plugin import SpyPlugin
from .bingo.plugin import BingoPlugin
from .trivia.plugin import TriviaPlugin

AVAILABLE_PLUGINS = [
    NumberGuessingPlugin,
    SpyPlugin,
    BingoPlugin,
    TriviaPlugin
]
