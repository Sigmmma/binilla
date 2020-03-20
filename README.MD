# Binilla
[![](https://img.shields.io/pypi/dm/binilla)](https://pypistats.org/packages/binilla)
![](https://ci.appveyor.com/api/projects/status/github/Sigmmma/binilla?svg=true)
[![PyPI version](https://badge.fury.io/py/binilla.svg)](https://pypi.org/project/binilla/)
[![GitHub version](https://badge.fury.io/gh/Sigmmma%2Fbinilla.svg)](https://github.com/Sigmmma/binilla)


Binilla is a universal, GUI based, binary structure editor for [supyr_struct](https://github.com/Sigmmma/supyr_struct). Binilla is capable of generating editing interfaces for any binary structures defined with the supyr_struct library. Meta data can be embedded into the supyr_struct descriptors to customize the way Binilla displays the structures. This includes specifying custom widgets, field value ranges, visibility of fields, whether a field can be edited, comments, tooltips, field units, and more.

Below are a few versions of Binilla displaying various structures. Even the configuration window is generated from a supyr_struct structure definition.

![](https://i.imgur.com/ztaByUS.png)
![](https://i.imgur.com/deF6W8T.png)

## Installing

You'll need Python 3.5 or higher.

In your terminal execute:
```sh
python3 -m pip install binilla
```
or, you can clone/download this repo and run the setup.py:
```sh
git clone git@github.com:Sigmmma/binilla.git
cd supyr_struct
python3 -m pip install .
```
## Who do I talk to?

If you're having any issues with the library you can report them on our [GitHub Issues page](https://github.com/Sigmmma/binilla/issues).

If the issue requires some more direct attention we'll drop a contact link.
