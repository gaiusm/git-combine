#!/usr/bin/env python3

# configure.py a configuration module used by git-combine
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


import fsalias
import os, sys


reservedTokens = ["des", "inc", "patchdir", "patches",
                  "combine", "git", "safedir", "shell",
                  "prepend", "allowed",
                  "log", "in", "do", "until"]

tokens = []
fileName, lineNumber = None, 1
debugging = False
desGit = None
incGit = None
currentDir = None
findLogFunc = None
createPatchesFunc = None
setPatchDirFunc = None


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print (str (format) % args, end=' ')


#
#  syntaxError - issues a syntax error and exits.
#

def syntaxError (message):
    global fileName, lineNumber
    print ("%s:%d:%s" % (fileName, lineNumber, message))
    sys.exit (1)


def safeSystem (format, *args):
    command = str (format) % args
    command += "\n"
    if os.system (command) != 0:
        printf ("error: system (%s) failed\n", command)
        sys.exit (1)


def setDes (des):
    global desGit
    desGit = des
    fsalias.setDesDir (des)
    return True


def setInc (inc):
    global incGit
    incGit = inc
    fsalias.setIncDir (inc)
    return True


def getDirectory ():
    if len (tokens) > 0:
        directory = getString ()
        return directory
    return None


def tokeniseString (line):
    line = " " + line + " "
    for token in reservedTokens:
        line = line.replace (" " + token + " ", " <" + token + "> ")
    return line.split ()


def tokeniseLine (line):
    global tokens

    line = line.rstrip ()
    orig = line
    line = line.split ("#")[0]
    i = line.find ('"""')
    while i >= 0:
        during = line[i+3:]
        j = during.find ('"""')
        if j >= 0:
            during = during[:j]
            before = line[:i]
            after = line[i+j+3+3:]
            # printf ("before = %s, during = %s, after = %s\n", before, during, after)
            tokens += tokeniseString (before)
            tokens += ['"""' + during + '"""']
            line = after
            i = line.find ('"""')
            # printf ("new line = %s\n", line)
        else:
            syntaxError ('end quote must be on the same line: ' + orig)
    tokens += tokeniseString (line)
    tokens += ["<lf>"]


#
#  pushTokens - pushes a list of tokens after it has tokenised them
#

def pushTokens (lines):
    global tokens
    for line in lines:
        tokeniseLine (line)
    tokens += ["<eof>"]


#
#  readFile - read in, name, convert it to a list of lines
#             and pass them to pushTokens.
#

def readFile (name):
    global fileName, lineNumber
    fileName = name
    lineNumber = 1
    try:
        pushTokens (open (name).readlines ())
    except:
        printf ("unable to open file: %s\n", name)
        sys.exit (1)


#
#  getToken - returns the first token from the token stream.
#

def getToken ():
    global tokens, lineNumber
    if len(tokens)>0:
        token = tokens[0]
        tokens = tokens[1:]
    else:
        token = "<eof>"
    if token == "<lf>":
        lineNumber += 1
        return getToken()
    if debugging:
        printf ("<<%s>> %s\n", token, tokens)
    return token


#
#  isToken - tests whether we can see, token, in the list of
#            tokens.
#

def isToken (token):
    global tokens, lineNumber
    if len(tokens) == 0:
        return token == "<eof>"
    else:
        if tokens[0] == "<lf>":
            lineNumber += 1
            tokens = tokens[1:]
            return isToken(token)
        if debugging:
            printf ("%s\n", tokens)
            printf ("testing whether: %s == %s\n", token, tokens[0])
        return tokens[0] == token


#
#  eat - consume a token and return True if the token
#        matched the current token.  It does not consume
#        a token if it did not match.
#

def eat (token):
    global tokens
    if isToken (token):
        getToken()
        if debugging:
            printf ("eat returning True, having found: %s\n", token)
        return True
    else:
        if debugging:
            printf ("eat returning False, having failed to find %s token is actually %s\n", token, tokens[0])
        return False


#
#  insist - consumes, token, from the token list and
#           generates an error message if this token
#           was not seen.
#

def insist (token):
    if debugging:
        printf ("insisting on: %s\n", token)
    if not eat (token):
        syntaxError("missing " + token)

#
#  ebnf
#

# desdef := "des" directory =:
# incdef := "inc" directory =:
# patchdirdef := "patchdir" directory =:
# indef := "in" ( "des" | "inc" ) "do" { indentedline } =:
# patchesdef := "patches" =:
# combinedef := "combine" =:


def safeChdir (name, git):
    if git == None:
        syntaxError ("git repository: " + name + " undefined")
    else:
        os.chdir (currentDir)
        if currentDir != os.getcwd ():
            syntaxError ("unable to move back to start directory: " + currentDir)
        os.chdir (git)


def inDef ():
    if eat ("<in>"):
        if eat ("<des>"):
            safeChdir ("des", desGit)
        elif eat ("<inc>"):
            safeChdir ("inc", incGit)
        else:
            printf ("looking at: %s\n", tokens[0])
            syntaxError ("expecting inc or des")
        if eat ("<do>"):
            return True
        syntaxError ("expecting do")
    return False


def desDef ():
    if eat ("<des>"):
        return setDes (getDirectory ())
    return False


def incDef ():
    if eat ("<inc>"):
        return setInc (getDirectory ())
    return False


def patchDirDef ():
    if eat ("<patchdir>"):
        setPatchDirFunc (getDirectory ())
        return True
    return False


def patchesDef ():
    if eat ("<patches>"):
        createPatchesFunc ()


def combineDef ():
    if eat ("<combine>"):
        fsalias.performCombine ()


def getString ():
    global tokens
    # printf ("checking for a string: %s\n", tokens[0])
    if (not isToken ("<eof>")) and (not isToken ("<lf>")):
        if (len (tokens[0]) > 3) and (tokens[0][:3] == '"""'):
            if (len (tokens) > 6) and (tokens[0][-3:] == '"""'):
                s = tokens[0][3:-3]
                tokens = tokens[1:]
                return s
    syntaxError ("string not found")


def gitDef ():
    if eat ("<git>"):
        s = getString ()
        # printf ("string = %s\n", s)
        safeSystem ("git %s", s)
        return True
    return False


def logDef ():
    if eat ("<log>"):
        return findLogFunc (getString ())
    return False


def setSafeDir ():
    if eat ("<safedir>"):
        fsalias.safeDir (getDirectory ())
        return True
    return False


def getHash ():
    return getString ()


def prependDef ():
    if eat ("<prepend>"):
        directory = getDirectory ()
        if eat ("<until>"):
            rsahash = getHash ()
        else:
            rsahash = None
        # printf ("prepend %s %s\n", directory, rsahash)
        fsalias.prependDir (directory, rsahash)
        return True
    return False


def allowedDef ():
    if eat ("<allowed>"):
        dir1 = getDirectory ()
        dir2 = getDirectory ()
        fsalias.allowedDir (dir1, dir2)
        return True
    return False

#
#  shellDef :- "shell" string
#

def shellDef ():
    if eat ("<shell>"):
        command = getString ()
        safeSystem (command)
        return True
    return False


def ebnf ():
    while not isToken ("<eof>"):
        # printf ("tokens[0] = %s\n", tokens[0])
        if desDef ():
            pass
        elif incDef ():
            pass
        elif patchDirDef ():
            pass
        elif patchesDef ():
            pass
        elif combineDef ():
            pass
        elif gitDef ():
            pass
        elif setSafeDir ():
            pass
        elif prependDef ():
            pass
        elif allowedDef ():
            pass
        elif inDef ():
            pass
        elif logDef ():
            pass
        elif shellDef ():
            pass
        else:
            # printf ("remaining tokens: ")
            # print (tokens)
            # printf ("\n")
            syntaxError ("unexpected token: " + tokens[0])


def config (name, findLog, createPatch, setPatch):
    global currentDir, findLogFunc, createPatchesFunc, setPatchDirFunc

    findLogFunc = findLog
    createPatchesFunc = createPatch
    setPatchDirFunc = setPatch
    readFile (name)
    currentDir = os.getcwd ()
    fsalias.setCurrentDir (currentDir)
    # print (tokens)
    # sys.exit (0)
    return ebnf ()
