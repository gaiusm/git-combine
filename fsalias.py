# fsalias.py a filesystem alias module used by git-combine
#
# Copyright (C) 2020 Free Software Foundation, Inc.
# Contributed by Gaius Mulley <gaius@glam.ac.uk>.
#
# This file is part of git-combine.
#
# git-combine is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# git-combine is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Modula-2; see the file COPYING.  If not, write to the
# Free Software Foundation, 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#


import os, sys, glob
    chCurDir ()
    oprintf ("}\n\n")
    oprintf ("function note () {\n")
    oprintf ("   echo -e \"\\e[34m$*\\e[0m\"\n")
    oprintf ("   return 0\n")
def chIncDir ():
    os.chdir (currentDir)
    os.chdir (incDir)


def chDesDir ():
    os.chdir (currentDir)
    os.chdir (desDir)


def chCurDir ():
    os.chdir (currentDir)


        chIncDir ()
        command = "git show %s -- %s > /tmp/fileperm\n" % (lastCommit, old)
        # printf ("command = %s\n", command)
            chCurDir ()
            next_line = False
            for line in open ("/tmp/fileperm", "rb").readlines ():
                line = line.decode ('ISO-8859-1')
                # printf ("line = %s\n", line)
                if starts_with (line, "diff --git"):
                    next_line = True
                elif next_line:
                    if starts_with (line, "new file mode"):
                        line = line.rstrip ()
                        perm = line.split ()[-1][3:]
                        oprintf ("note changing file permissions of %s to %s\n", new, perm)
                        oprintf ("chmod %s %s\n", perm, new)
                        return
        filename = "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        filename = os.path.join (patchDirectory, filename)
        chIncDir ()
        filename = "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        filename = os.path.join (patchDirectory, filename)
        chIncDir ()
        patchfile = "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        patchfile = os.path.join (patchDirectory, patchfile)
        chIncDir ()
        oprintf ("cp -p %s %s || error cp %s %s\n", patchfile, fs[fullname], patchfile, fs[fullname])
        chCurDir ()
        filename = "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        filename = os.path.join (patchDirectory, filename)
        chIncDir ()
    filename = "%06d.commit-log" % (commitPatchNo)
    filename = os.path.join (patchDirectory, filename)
    filename = "%06d.commit-log" % (commitPatchNo)
    filename = os.path.join (patchDirectory, filename)
def performCombine ():
    chCurDir ()
    patchList = glob.glob ("%s/*.sh" % (patchDirectory))
    patchList.sort ()
    chDesDir ()
    count = 0
    total = 0
    for p in reversed (patchList):
        safeSystem ("pwd")
        safeSystem ("bash %s", p)
        safeSystem ("pwd")
        count += 1
        total += 1
        if count == 10:
            printf ("total scripts applied: %d\n", total)
            count = 0