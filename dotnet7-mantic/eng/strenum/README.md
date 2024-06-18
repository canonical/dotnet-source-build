# StrEnum

A Python `enum.Enum` that inherits from `str` to complement
`enum.IntEnum` in the standard library. Supports python 3.7+.

- [Repository](https://github.com/irgeek/StrEnum)
- [Doumentation](https://strenum.readthedocs.io/en/latest/index.html)
- [Project on Pip](https://pypi.org/project/StrEnum/)

## Rationale

Starting with Python 3.11, `enum.StrEnum` is available in the standard
library, but Ubuntu 22.04 (Jammy Jellyfish) only ships with Python 3.10.

To keep the behaviour of a `enum.StrEnum` for Python 3.10+, a copy of this
popular backport is included. This especially allows to avoid adding `.value`
to every Enum instance to improve readability.

## LICENSE

Copyright (c) 2019 James C Sinclair

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
