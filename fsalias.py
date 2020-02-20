#!/usr/bin/env python3

#
#  a module to implement a filesystem alias
#  it allows the callee to create files and directories which are aliased to
#  other locations.
#

import os, sys

poisonedDirs = []
altDir = ""
fs = {}
allowedDirs = []
commitAuthor = None
commitDate = None
commitPatchNo = 0
patchOpen = False
patchDirectory = "."
output = sys.stdout
oldStdout = sys.stdout
lastCommit = None
commitLog = ""
commitFile = "/tmp/commitmessage"
existingDirs = []
prependDirs = []


import codecs

def slashescape(err):
    """ codecs error handler. err is UnicodeDecode instance. return
    a tuple with a replacement for the unencodable part of the input
    and a position where encoding should continue"""
    thebyte = err.object[err.start:err.end]
    repl = u'\\x'+hex (ord (thebyte))[2:]
    return (repl, err.end)

codecs.register_error ('slashescape', slashescape)


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    sys.stdout.write (str (format) % args)
    sys.stdout.flush ()


def oprintf (format, *args):
    global output
    output.write (str (format) % args)
    output.flush ()


def safeSystem (format, *args):
    command = str (format) % args
    command += " || exit 1\n"
    if os.system (command) != 0:
        printf ("error: system (%s) failed\n", command)
        sys.exit (1)

#
#
#

def prependDir (directory, until):
    global prependDirs
    prependDirs = [directory, until]


def prepend (directory):
    if prependDirs == []:
        return directory
    return os.path.join (prependDirs[0], directory)


def checkPrepend (rsa):
    global prependDirs
    if (prependDirs != []) and (prependDirs[1] == rsa):
        prependDirs = []


#
#
#

def initPatch ():
    global commitPatchNo, patchOpen, output, commitAuthor, commitDate, commitFileNo
    commitPatchNo +=1
    d = patchDirectory + "/patch-scripts"
    safeSystem ("mkdir -p %s", d)
    d += "/%06d.sh"
    d = d % commitPatchNo
    printf ("[%06d]\n", commitPatchNo)
    output = open (d, "w")
    oprintf ("#!/bin/bash\n\n")
    commitDate = None
    commitAuthor = None
    commitFileNo = 1


def finishPatch ():
    global output
    output.flush ()
    output.close ()


#
#  allowedDir - a directory in which files and directories can be created.
#

def allowedDir (topstrip, allowed):
    global allowedDirs
    allowedDirs += [[topstrip, allowed]]


#
#  safeDir - the directory under which the aliased files are created.
#

def safeDir (d):
    global altDir
    altDir = d


def patchDir (d):
    global patchDirectory
    patchDirectory = d

#
#  findPathName - returns the [filename, path]
#

def findPathName (name):
    f = name.split (os.path.sep)[-1]
    p = ""
    for c in name.split (os.path.sep)[:-1]:
        p = os.path.join (p, c)
    return p, f


def copyContents (src, dest, gitdirfile = None):
    global commitFileNo
    if lastCommit == None:
        pass
    else:
        filename = patchDirectory + "/patch-scripts/"
        filename += "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        commitFileNo += 1
        if gitdirfile == None:
            safeSystem ("git show %s:%s > %s", lastCommit, src, filename)
        else:
            safeSystem ("git show %s:%s > %s", lastCommit, gitdirfile, filename)
        dest = stripAllowed (dest)
        makeDir (extractPath (dest))
        oprintf ("cp -p %s %s || exit 1\n", filename, dest)
        output.flush ()


def makeDir (path):
    global existingDirs
    if True:
        # if not (path in existingDirs):
        oprintf ("mkdir -p %s\n", path)
        oprintf ("git add %s\n", path)
        return
        existingDirs += [path]
        p = "."
        for c in path.split (os.path.sep):
            p = os.path.join (p, c)
            oprintf ("git add %s\n", p)


def extractPath (filename):
    p, f = findPathName (filename)
    return p


def git_sh_create (fullname, path, filename):
    makeDir (path)
    combined = os.path.join (path, filename)
    copyContents (fullname, combined)
    oprintf ("git add %s   # git_sh_create\n", combined)


def temp_git_sh_create (temp, path, filename):
    combined = os.path.join (path, filename)
    makeDir (extractPath (temp))
    copyContents (combined, temp)
    oprintf ("git add %s  # temp_git_sh_create %s\n", temp, lastCommit)


def starts_with (line, word):
    if (len (line) == len (word)) and (line == word):
        return True
    if (len (line) > len (word)) and (line[:len (word)] == word):
        return True
    return False


def top_strip (d):
    if (len (d) > 1) and (d[0] == "/"):
        return d[1:]
    if (len (d) == 2) and (d == "./"):
        return ""
    if (len (d) > 2) and (d[:2] == "./"):
        return d[2:]
    return d


def isAllowed (d):
    orig = top_strip (d)
    for top, allowed in allowedDirs:
        d = orig
        if starts_with (d, top):
            d = d[len (top):]
            d = top_strip (d)
            if starts_with (d, allowed):
                return True
    return False


def stripAllowed (d):
    orig = top_strip (d)
    if isAllowed (orig):
        for top, allowed in allowedDirs:
            d = orig
            if starts_with (d, top):
                return top_strip (d[len (top):])
    return d


#
#  create - creates file called name.
#

def create (fullname):
    global fs
    printf ("create:  %s\n", fullname)
    path, filename = findPathName (prepend (fullname))
    if isAllowed (path):
        path = stripAllowed (path)
        git_sh_create (fullname, path, filename)
    else:
        fs[fullname] = os.path.join (os.path.join (altDir, path), filename)
        temp_git_sh_create (fs[fullname], path, filename)


def modify (fullname):
    path, filename = findPathName (prepend (fullname))
    if fullname in fs:
        copyContents (fs[fullname], fs[fullname], fullname)
    else:
        copyContents (fullname, prepend (fullname))


#
#  rm - deletes file called name.
#

def rm (fullname):
    global fs
    fullname = prepend (fullname)
    if fullname in fs:
        oprintf ("git rm %s\n", fs[fullname])
        del fs[fullname]
    else:
        fullname = stripAllowed (fullname)
        oprintf ("git rm %s\n", fullname)


#
#  mv - move file src to dest.
#

def mv (src, dest):
    global fs
    src = prepend (src)
    dest = prepend (dest)
    if src in fs:
        new_src = fs[src]
        del fs[src]
        src = new_src
    path, filename = findPathName (dest)
    if isAllowed (path):
        path = stripAllowed (path)
        dest = stripAllowed (dest)
        src = stripAllowed (src)
        makeDir (path)
        oprintf ("if [ ! -f %s ] ; then exit 1 ; fi\n", src)
        oprintf ("git mv %s %s || exit 1\n", src, dest)
    else:
        fs[dest] = os.path.join (os.path.join (altDir, path), filename)
        makeDir (os.path.join (altDir, path))
        oprintf ("if [ ! -f %s ] ; then exit 1 ; fi\n", src)
        oprintf ("git mv %s %s || exit 2\n", src, fs[dest])
        path, filename = findPathName (src)
        # oprintf ("git rm %s\n", path)


def author (name):
    global commitAuthor
    commitAuthor = name
    # printf ("Author: %s\n", commitAuthor)


def date (name):
    global commitDate
    commitDate = name
    # printf ("Date: %s\n", commitDate)


def commitMessage (msg):
    global commitLog
    commitLog = msg + "\n" + commitLog


def addAll (directory):
    oprintf ("if [ -d %s ] ; then git add --all %s ; fi\n", directory, directory)


def commit (rsa):
    global lastCommit, commitLog

    addAll ("gcc/gm2")
    addAll ("gcc/m2")
    addAll ("gcc/testsuite")
    lastCommit = rsa
    filename = patchDirectory + "/patch-scripts/"
    filename += "%06d.commit-log" % (commitPatchNo)
    f = open (filename, 'w')
    f.write (commitLog)
    f.close ()
    command = "git commit"
    if commitDate != None:
        command += " --date="
        command += "\""
        command += commitDate
        command += "\""
    if commitAuthor != None:
        command += " --author="
        command += "\""
        command += commitAuthor
        command += "\""
    command += " -F "
    command += filename
    command += " -a\n"
    oprintf (command)
    oprintf ("echo %s\n", commitDate)
    finishPatch ()
    initPatch ()
    commitLog = ""
    checkPrepend (rsa)


def nextCommit (rsa):
    global lastCommit
    lastCommit = rsa


# create ("dir/this/that/file.c")
