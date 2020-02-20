#!/usr/bin/env python3

#
#  a script to merge two repositories together
#  (the gm2 repository and the gcc repository).
#  It builds:
#     * list of commits for each branch
#     * a commit will consist of a patch and optionally
#       file move/new file
#
#  The script can be run between two hashes (or across the whole log)
#  although in the case of gm2 the script is only run over a DAG.
#  The DAG start/end points are either the start of a branch
#  or when the directory level of gcc/m2 in the repository changes.
#

findBranches      = 'git branch -a'
findBranchStart   = 'git merge-base master'
findBranchCommits = 'git log master..remotes/origin/gcc_9_2_0_gm2'
findBranchHistory = 'git log --name-status'
logFile           = '/tmp/branch-log'

debugging = False
patchDir = None
reproDir = None
configFile = None


import os, sys, getopt, fsalias, glob, configure


def usage (code):
    print ("git-combine [-v][-h] startdir")
    sys.exit (code)


def handleOptions ():
    global patchDir, reproDir, configFile
    optlist, l = getopt.getopt (sys.argv[1:], ':vhd:f:r:')
    print ("optlist =", optlist)
    print ("list =", l)
    for opt in optlist:
        print (opt)
        if opt[0] == '-h':
            usage (0)
        if opt[0] == '-v':
            print ("verbose found")
        if opt[0] == '-d':
            patchDir = opt[1]
        if opt[0] == '-r':
            reproDir = opt[1]
        if opt[0] == '-f':
            configFile = opt[1]


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print (str (format) % args, end=' ')


#
#  fatal - displays a message and exits
#

def fatal (format, *args):
    print (str (format) % args, end=' ')
    os.sys.exit (1)


def localSystem (s):
    if debugging:
        printf (s)
    os.system (s)


def getBranchList () :
    localSystem (findBranches + ' > /tmp/branch-list')
    branches = []
    for lines in open ('/tmp/branch-list', 'r').readlines ():
        l = lines.lstrip ()
        words = l.split ()
        if words[0] == '*':
            branches += [words[1]]
        else:
            branches += [words[0]]
    return branches


def getBranchStart (branch):
    localSystem (findBranchStart + ' ' + branch + ' > /tmp/branch-start')
    start = open ('/tmp/branch-start', 'r').readline ()
    return start


def findLog (branch):
    branchList = getBranchList ()
    for b in branchList:
        printf ("branch %s starts at %s\n", b, getBranchStart (b))
        if b == branch:
            localSystem (findBranchHistory + ' ' + branch + ' > /tmp/branch-log')
            return True
    return False


def isDigit (ch):
    return ch in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def isNumCode (line, code):
    if (len (line) > len (code)) and (line[:len (code)] == code):
        line = line[len (code):]
        while isDigit (line[0]) and len (line) > 1:
            line = line[1:]
    return (len (line) > 1) and ((line[0] == " ") or (line[0] == "\t"))


def isCode (line, code):
    codewhite = code + "\t"
    if (len (line) > len (codewhite)) and (line[:len (codewhite)] == codewhite):
        return True
    codewhite = code + " "
    if (len (line) > len (codewhite)) and (line[:len (codewhite)] == codewhite):
        return True
    return False


def reversePatches ():
    files = glob.glob ("%s/*.sh" % (patchDir))
    files.sort ()
    n = len (files)
    for i in range (int (n/2)):
        j = n-i-1
        os.system ("mv %s t" % (files[i]))
        os.system ("mv %s %s" % (files[j], files[i]))
        os.system ("mv t %s" % (files[j]))


def peepCommit (num, lines):
    if num <= len (lines):
        for line in lines[num:]:
            line = line.decode ('ISO-8859-1')
            line = line.rstrip ()
            if isCode (line, 'commit'):
                fsalias.nextCommit (line.split ()[-1])
                return


def createDAGList (logfile):
    os.system ("rm -rf patch-scripts")
    fsalias.initPatch ()
    lines = open (logfile, "rb").readlines ()
    lines.reverse ()
    peepCommit (0, lines)
    for num, line in enumerate (lines):
        line = line.decode ('ISO-8859-1')
        line = line.rstrip ()
        if (len (line) == 0) or (line != line.lstrip ()):
            fsalias.commitMessage (line)
        elif isCode (line, 'M'):
            fsalias.modify (line.split ()[-1])
        elif isCode (line, 'A'):
            fsalias.create (line.split ()[-1])
        elif isCode (line, 'D'):
            # printf ("delete file: %s\n", line)
            fsalias.rm (line.split ()[-1])
        elif isNumCode (line, 'R1') or isNumCode (line, 'R0'):
            # printf ("mv file: %s\n", line)
            fsalias.mv (line.split ()[-2], line.split ()[-1])
        elif isCode (line, 'commit'):
            fsalias.commit (line.split ()[-1])
            peepCommit (num+1, lines)
        elif isCode (line, 'Date:'):
            line = line.lstrip ()
            fsalias.date (" ".join (line.split ()[1:]))
        elif isCode (line, 'Author:'):
            line = line.lstrip ()
            fsalias.author (" ".join (line.split ()[1:]))
        elif isCode (line, "Merge:"):
            printf ("merge: %s\n", line)
        else:
            printf ("unknown: %s\n", line)
            sys.exit (1)
    fsalias.finishPatch ()
    reversePatches ()


def createPatches ():
    if patchDir == None:
        printf ("patchDir has not been set\n")
        sys.exit (1)
    else:
        # os.system ("rm -rf " + patchDir)
        os.system ("pwd")
        printf ("should we: rm -rf %s\n", patchDir)
    fsalias.initPatch ()
    lines = open (logFile, "rb").readlines ()
    lines.reverse ()
    peepCommit (0, lines)
    for num, line in enumerate (lines):
        line = line.decode ('ISO-8859-1')
        line = line.rstrip ()
        if (len (line) == 0) or (line != line.lstrip ()):
            fsalias.commitMessage (line)
        elif isCode (line, 'M'):
            fsalias.modify (line.split ()[-1])
        elif isCode (line, 'A'):
            fsalias.create (line.split ()[-1])
        elif isCode (line, 'D'):
            # printf ("delete file: %s\n", line)
            fsalias.rm (line.split ()[-1])
        elif isNumCode (line, 'R1') or isNumCode (line, 'R0'):
            # printf ("mv file: %s\n", line)
            fsalias.mv (line.split ()[-2], line.split ()[-1])
        elif isCode (line, 'commit'):
            fsalias.commit (line.split ()[-1])
            peepCommit (num+1, lines)
        elif isCode (line, 'Date:'):
            line = line.lstrip ()
            fsalias.date (" ".join (line.split ()[1:]))
        elif isCode (line, 'Author:'):
            line = line.lstrip ()
            fsalias.author (" ".join (line.split ()[1:]))
        elif isCode (line, "Merge:"):
            printf ("merge: %s\n", line)
        else:
            printf ("unknown: %s\n", line)
            sys.exit (1)
    fsalias.finishPatch ()
    reversePatches ()


def setPatchDir (directory):
    global patchDir
    patchDir = directory
    fsalias.patchDir (patchDir)


def main ():
    handleOptions ()
    if configFile != None:
        configure.config (configFile, findLog, createPatches, setPatchDir)


def oldmain ():
    fsalias.patchDir (patchDir)
    findLog (branchList[0])
    fsalias.reproDir (reproDir)
    fsalias.safeDir ("gcc/m2/pre")
    # fsalias.prependDir ("gcc-versionno/gcc/gm2", "1e269d8cfa1d57f0e508e43d327827fe15fc1b57")
    # fsalias.prependDir ("gcc-versionno/gcc/gm2", "7750ae1a859853ec2cd7c12147218bca4364af55")
    fsalias.prependDir ("gcc-versionno/gcc/gm2", "d493ab1cc34f7d11ec79387bbd0b375c8494a644")
    fsalias.allowedDir ("gcc-versionno", "gcc/m2")
    fsalias.allowedDir ("gcc-versionno", "gcc/gm2")
    fsalias.allowedDir ("gcc-versionno", "gcc/testsuite/gm2")
    fsalias.allowedDir ("gcc-versionno", "gcc/testsuite/lib")
    fsalias.allowedDir ("gcc-versionno", "libgm2")

    createDAGList ('/tmp/branch-log')


main ()
