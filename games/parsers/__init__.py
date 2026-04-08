from .bracket_city import BracketCityParser
from .connections import ConnectionsParser

# Add new game parsers here — order matters (first match wins).
PARSERS = [
    BracketCityParser(),
    ConnectionsParser(),
]
