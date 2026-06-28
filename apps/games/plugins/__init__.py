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

# Wave 3
from .mafia.plugin import MafiaPlugin
from .werewolf.plugin import WerewolfPlugin
from .memory_match.plugin import MemoryMatchPlugin
from .spot_the_difference.plugin import SpotTheDifferencePlugin
from .word_chain.plugin import WordChainPlugin
from .hangman.plugin import HangmanPlugin
from .categories.plugin import CategoriesPlugin

AVAILABLE_PLUGINS = [
    NumberGuessingPlugin,
    SpyPlugin,
    BingoPlugin,
    TriviaPlugin,
    BusCompletePlugin,
    DrawAndGuessPlugin,
    CharadesPlugin,
    PasswordPlugin,
    TabooPlugin,
    MafiaPlugin,
    WerewolfPlugin,
    MemoryMatchPlugin,
    SpotTheDifferencePlugin,
    WordChainPlugin,
    HangmanPlugin,
    CategoriesPlugin
]
