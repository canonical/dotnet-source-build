import re
from zlib import crc32

class _NameMangler:
    def words(self, name: str) -> str: ...
    def camel(self, name: str) -> str: ...
    def pascal(self, name: str) -> str: ...
    def kebab(self, name: str) -> str: ...
    def snake(self, name: str) -> str: ...
    def macro(self, name: str) -> str: ...
    def camel_snake(self, name: str) -> str: ...
    def pascal_snake(self, name: str) -> str: ...
    def spongebob(self, name: str) -> str: ...
    def cobol(self, name: str) -> str: ...
    def http_header(self, name: str) -> str: ...
