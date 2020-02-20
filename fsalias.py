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
prependSrcDir = ""
debugFiles = False


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
    varargs = str (format) % args
    command = varargs
    command += " || error "
    command += varargs
    command += " failed\n"
    if os.system (command) != 0:
        printf ("error: system (%s) failed\n", command)
        sys.exit (1)


def reproDir (directory):
    global repDir
    repDir = directory


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
    global prependDirs, prependSrcDir
    if (prependDirs != []) and (prependDirs[1] == rsa):
        prependSrcDir = prependDirs[0]
        prependDirs = []


def prependSrc (directory):
    if prependDirs == []:
        if prependSrcDir == "":
            return directory
        oprintf ("# prepending src special case\n")
        return os.path.join (prependSrcDir, directory)
    else:
        return prepend (directory)

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
    oprintf ("function error () {\n")
    oprintf ("   echo -e \"\\e[31m$*\\e[0m\"\n")
    oprintf ("   return 0\n")
    oprintf ("}\n")
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


def correctPermissions (old, new):
    if lastCommit != None:
        printf ("chmod called (%s, %s)\n", old, new)
        cwd = os.getcwd ()
        os.chdir (repDir)
        command = "git ls-files %s --stage %s > /tmp/fileperm\n" % (lastCommit, old)
        printf ("command = %s\n", command)
        if os.system (command) == 0:
            os.chdir (cwd)
            line = open ("/tmp/fileperm", "r").readline ()
            line = line.lstrip ()
            printf ("line = %s\n", line)        
            if line == "":
                printf ("file %s is not in the repro\n", old)
            else:
                perm = line.split ()[0][3:]
                safeSystem ("chmod %s %s\n", perm, new)


def copyContents (src, dest):
    if debugFiles:
        return pseudoCopyContents (src, dest)
    else:
        return realCopyContents (src, dest)


def realCopyContents (src, dest):
    global commitFileNo, fs
    if lastCommit != None:
        filename = patchDirectory + "/patch-scripts/"
        filename += "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        commitFileNo += 1
        oprintf ("# real copy contents\n")
        safeSystem ("git show %s:%s > %s", lastCommit, src, filename)        
        if isAllowed (dest):
            dest = stripAllowed (dest)
            makeDir (extractPath (dest))
        else:
            path, destfile = findPathName (dest)
            fs[dest] = os.path.join (os.path.join (altDir, path), destfile)
            dest = fs[dest]
            makeDir (extractPath (dest))
        oprintf ("cp -p %s %s || error cp %s %s\n", filename, dest, filename, dest)
        correctPermissions (src, dest)
        output.flush ()
    return dest


def pseudoCopyContents (src, dest, gitdirfile):
    if lastCommit != None:
        dest = stripAllowed (dest)
        makeDir (extractPath (dest))
        oprintf ("touch %s\n", dest)
        output.flush ()
    return dest

def copyKnown (src, dest):
    global commitFileNo
    if lastCommit != None:
        oprintf ("# copy known\n")
        filename = patchDirectory + "/patch-scripts/"
        filename += "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        commitFileNo += 1
        safeSystem ("git show %s:%s > %s", lastCommit, src, filename)
        makeDir (extractPath (dest))
        oprintf ("cp -p %s %s || error cp %s %s\n", filename, dest, filename, dest)
        correctPermissions (src, dest)
        oprintf ("git add %s\n", dest)
        output.flush ()


def makeDir (path):
    if debugFiles:
        pseudoMakeDir (path)
    else:
        realMakeDir (path)


def pseudoMakeDir (path):
    oprintf ("mkdir -p %s\n", path)


def realMakeDir (path):
    global existingDirs
    oprintf ("mkdir -p %s\n", path)
    oprintf ("git add %s\n", path)


def extractPath (filename):
    p, f = findPathName (filename)
    return p


def git_sh_create (fullname, path, filename):
    makeDir (path)
    combined = os.path.join (path, filename)
    dest = copyContents (fullname, combined)
    if not debugFiles:
        oprintf ("git add %s   # git_sh_create\n", dest)


def temp_git_sh_create (temp, path, filename):
    combined = os.path.join (path, filename)
    makeDir (extractPath (temp))
    dest = copyContents (combined, temp)
    if not debugFiles:
        oprintf ("git add %s  # temp_git_sh_create %s\n", dest, lastCommit)


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
    global commitFileNo, fs
    oprintf ("#\n")
    oprintf ("# create %s\n", fullname)
    oprintf ("#\n")
    path, filename = findPathName (prepend (fullname))
    if isAllowed (path):
        oprintf ("# isAllowed %s\n", path)
        path = stripAllowed (path)
        combined = os.path.join (path, filename)
        restoreFile (fullname, combined)
    else:
        fs[fullname] = os.path.join (os.path.join (altDir, path), filename)
        oprintf ("#   held temporarily in %s\n", fs[fullname])
        patchfile = patchDirectory + "/patch-scripts/"
        patchfile += "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        commitFileNo += 1
        safeSystem ("git show %s:%s > %s", lastCommit, fullname, patchfile)
        makeDir (extractPath (fs[fullname]))
        oprintf ("cp -p %s %s || error cp %s %s\n", patchfile, fs[fullname],  patchfile, fs[fullname])
        correctPermissions (fullname, fs[fullname])
        oprintf ("git add %s\n", fs[fullname])
    oprintf ("# completed create\n")


def modify (fullname):
    path, filename = findPathName (prepend (fullname))
    if fullname in fs:
        copyKnown (fullname, fs[fullname])
    else:
        dest = copyContents (fullname, prepend (fullname))
        oprintf ("# no need to add %s as it is already known\n", dest)


#
#  rm - deletes file called name.
#

def rm (fullname):
    if debugFiles:
        pseudoRm (fullname)
    else:
        realRm (fullname)


#
#  realRm - deletes file called name.
#

def realRm (fullname):
    global fs
    fullname = prepend (fullname)
    if fullname in fs:
        oprintf ("git rm %s\n", fs[fullname])
        del fs[fullname]
    else:
        path, filename = findPathName (prepend (fullname))
        if isAllowed (path):
            fullname = stripAllowed (fullname)
            oprintf ("git rm %s\n", fullname)
        else:
            oprintf ("echo odd as %s is not allowed and is not in the fsalias\n", fullname)


#
#  pseudoRm - deletes file called name.
#

def pseudoRm (fullname):
    global fs
    fullname = prepend (fullname)
    if fullname in fs:
        oprintf ("rm %s\n", fs[fullname])
        del fs[fullname]
    else:
        fullname = stripAllowed (fullname)
        oprintf ("rm %s\n", fullname)


#
#  mv - move file src to dest.
#

def mv (src, dest):
    if debugFiles:
        pseudoMv (src, dest)
    else:
        realMv (src, dest)

def translate (path, src = False):
    global fs
    if src:
        if path in fs:
            oprintf ("# %s is in aliasfs\n", path)
            new_path = fs[path]
            del fs[path]
            return new_path
        else:
            path = prependSrc (path)
    else:
        path = prepend (path)
    return stripAllowed (path)


def makeMv (src, dest):
    oprintf ("if [ ! -f %s ] ; then error mv src %s does not exist ; fi\n", src, src)
    oprintf ("git mv %s %s || error git mv dest into non existant directory %s\n", src, dest, extractPath (dest))


def restoreFile (oldrepro, combined):
    global commitFileNo, fs
    if lastCommit != None:
        filename = patchDirectory + "/patch-scripts/"
        filename += "%06d-%02d.contents" % (commitPatchNo, commitFileNo)
        commitFileNo += 1
        safeSystem ("git show %s:%s > %s", lastCommit, oldrepro, filename)
        makeDir (extractPath (combined))
        oprintf ("cp -p %s %s || error cp %s %s\n", filename, combined, filename, combined)
        correctPermissions (oldrepro, combined)
        oprintf ("git add %s\n", combined)


def realMv (src, dest):
    global fs
    oprintf ("#\n")
    oprintf ("# mv %s %s\n", src, dest)
    oprintf ("#\n")
    src = translate (src, True)
    path, filename = findPathName (prepend (dest))
    if isAllowed (path):
        oprintf ("# isAllowed %s\n", path)
        path = stripAllowed (path)
        combined = os.path.join (path, filename)
        makeDir (extractPath (combined))
        makeMv (src, combined)
        # just in case get the contents from git.
        restoreFile (dest, combined)
    else:
        oprintf ("# not allowed %s  (%s)\n", path, dest)
        fs[dest] = os.path.join (os.path.join (altDir, path), filename)
        makeDir (os.path.join (altDir, path))
        makeMv (src, fs[dest])
    oprintf ("# completed mv\n")


def pseudoMv (src, dest):
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
        oprintf ("mv %s %s || exit 1\n", src, dest)
    else:
        fs[dest] = os.path.join (os.path.join (altDir, path), filename)
        makeDir (os.path.join (altDir, path))
        oprintf ("if [ ! -f %s ] ; then exit 1 ; fi\n", src)
        oprintf ("mv %s %s || exit 2\n", src, fs[dest])
        path, filename = findPathName (src)
        oprintf ("rm %s\n", src)


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
    if not debugFiles:
        oprintf ("if [ -d %s ] ; then git add --all %s ; fi\n", directory, directory)


def commit (rsa):
    if debugFiles:
        pseudoCommit (rsa)
    else:
        realCommit (rsa)


def realCommit (rsa):
    global lastCommit, commitLog, prependSrcDir

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
    if prependSrcDir != "":
        prependSrcDir = ""
    checkPrepend (rsa)


def pseudoCommit (rsa):
    lastCommit = rsa
    filename = patchDirectory + "/patch-scripts/"
    filename += "%06d.commit-log" % (commitPatchNo)
    finishPatch ()
    initPatch ()
    commitLog = ""
    oprintf ("echo end of script %06d.sh commit: %s\n", commitPatchNo, commitDate)
    checkPrepend (rsa)


def nextCommit (rsa):
    global lastCommit
    lastCommit = rsa


# create ("dir/this/that/file.c")
