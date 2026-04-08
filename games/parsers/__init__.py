from .bracket_city import BracketCityParser
from .connections import ConnectionsParser
from .wordle import WordleParser

# Add new game parsers here — order matters (first match wins).
PARSERS = [
    BracketCityParser(),
    ConnectionsParser(),
    WordleParser(),
]
