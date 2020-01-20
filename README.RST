Binilla
=======

What is this repository for?
----------------------------

- Binilla is a universal, GUI based, binary structure editor powered by `supyr_struct <https://bitbucket.org/Moses_of_Egypt/supyr_struct>`_. Binilla is capable of generating editing interfaces for any binary structures defined with the supyr_struct library. Meta data can be embedded into the supyr_struct descriptors to customize the way Binilla displays the structures. This includes specifying custom widgets, field value ranges, visibility of fields, whether a field can be edited, comments, tooltips, field units, and more.

- Below are a few versions of Binilla displaying various structures. Even the configuration window is generated from a supyr_struct structure definition.

.. image:: https://bitbucket.org/repo/4xyAzp/images/1451182705-binilla%20test1.png
.. image:: https://bitbucket.org/repo/4xyAzp/images/2229544774-binilla%20test2.PNG

Installing
----------

First install any version of Python 3(The newest version is recommended).

There are two ways to install binilla from this point:

-    Open a command prompt and execute: ``pip install binilla``


or

-    Extract a copy of the repository into a directory titled "binilla ".
-    Move the file "setup.py" into the directory containing "binilla ".
-    Open a command prompt, navigate to the directory containing setup.py, and execute: ``python setup.py install``
-    During install, python should try to download and install supyr_struct. If it fails to, you must install that as well.

Once the install finishes, binilla should be able to be run by opening a python interpreter and executing: ``from binilla import run``

Who do I talk to?
-----------------

- Devin Bobadilla (Author of binilla) mosesbobadilla@gmail.com