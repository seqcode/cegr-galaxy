Galaxy ChIP-exo - The Center for Eukaryotic Gene Regulation
===========================================================

This repository contains Galaxy components used by the labs in the Center for Eukaryotic Gene Regulation
at the Pennsylvania State University.

Python Standards
================

1) Galaxy follows PEP-8, with particular emphasis on the parts about knowing when to be consistent,
and readability being the ultimate goal.  One divergence from PEP-8 is line length. Logical (non-comment)
lines should be formatted for readability, recognizing the existence of wide screens and scroll bars
(sometimes a 200 character line is more readable, though rarely).

2) Use spaces, not tabs for indenting!  4 spaces per indent.

3) File names must never include capital letters, and words must be separated by underscore.  For example,
thisIsWrong.py and this_is_right.py.

4) Comments and documentation comments should follow the 79 character per line rule.

5) Python docstrings need to be reStructured Text (RST) and Sphinx markup compatible. See
https://wiki.galaxyproject.org/Develop/SourceDoc for more information.

6) Avoid from module import *. It can cause name collisions that are tedious to track down.

Meta-standards
==============

If you want to add something here, submit is as a Merge Request so that another developer can review it before
it is incorporated.
.
These are best practices. They are not rigid. There are no enforcers.
