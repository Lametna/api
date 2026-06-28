# Registry of all Wave 1 & 2 Games
from .number_guessing.plugin import NumberGuessingPlugin
from .spy.plugin import SpyPlugin
from .bingo.plugin import BingoPlugin
from .trivia.plugin import TriviaPlugin

# Wave 2
from .bus_complete.plugin import BusCompletePlugin
from .draw_and_guess.plugin import DrawAndGuessPlugin
from .charades.plugin import CharadesPlugin
from .password.plugin import PasswordPlugin
from .taboo.plugin import TabooPlugin

AVAILABLE_PLUGINS = [
    NumberGuessingPlugin,
    SpyPlugin,
    BingoPlugin,
    TriviaPlugin,
    BusCompletePlugin,
    DrawAndGuessPlugin,
    CharadesPlugin,
    PasswordPlugin,
    TabooPlugin
]
