#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import subprocess
import argparse
import re
import shlex

# set the os specific commands
if os.name == "nt":
    charset = "cp1252"
else:
    charset = "utf-8"


def calculate(cmd_line, args):
    for i in range(len(args)):
        cmd_line = cmd_line.replace("{" + str(i) + "}", str(args[i]))
    print(cmd_line)
    os.system(cmd_line)


# tricky: allows e.g. the complexitycalculator to do some calculations via command line and returns the result by -yamlraw as stdout stream  without the need to generate temporary result files


def executeAsStream(cmd_line, args):
    for i in range(len(args)):
        cmd_line = cmd_line.replace("{" + str(i) + "}", args[i])
    print(cmd_line)

    """from https://stackoverflow.com/a/38666645
    """
    p = subprocess.run(
        cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return p.stdout


def executeAsCallback(cmd_line, config, active_dir, call_back):
    """der Versuch einer subprocess Kommunikation über stdin/out (https://stackoverflow.com/a/4417735)
    starts the process, feeds his stdin with the content of 'config' and calls 'call_back' which each line
    received from process

    when process is finished, call_back is called a last time with a 'None' value to indicate that the process has finished
    """
    print(cmd_line)
    cwd = "."
    if active_dir:
        cwd = active_dir
    with subprocess.Popen(
        cmd_line,
        shell=True,
        stdout=subprocess.PIPE,
        cwd=cwd,
        stdin=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    ) as p:
        p.stdin.write(config)
        # laut https://gist.github.com/waylan/2353749 muss man wirklich stdin schliessen, damit's beim Client ankommt.
        # Damit ist jede echte Kommunikation mit dem Client wohl mit der Methode hinfällig...
        p.stdin.close()
        for line in p.stdout:
            if call_back:
                call_back(line)
    if call_back:
        call_back(None, p.returncode)
    if p.returncode != 0:
        pass  # raise CalledProcessError(p.returncode, p.args)


allLines = []
allLinesContains = False


def collectLines(line, return_code=0):
    global allLines, allLinesContains, charset,args
    if line == None:
        return
    pattern = re.compile(".*#!# jtp #!#\s*(\S+)\s*#!#\s*(.*)")
    match = pattern.match(line)
    if match:
        # print("matching!:", line, match.group())
        if allLinesContains:  # it's not just empty
            output = match.group(1)
            cmd_line = match.group(2)
            if output != "-":
                with open(output, "w") as fout:
                    for line in allLines:
                        fout.write(line)
                if cmd_line != "-":
                    os.system(match.group(2))
            else:
                if cmd_line != "-":
                    # print(shlex.split(cmd_line))
                    with subprocess.Popen(
                        shlex.split(cmd_line), cwd=args.directory , shell=True, stdin=subprocess.PIPE
                    ) as p:
                        for line in allLines:
                            p.stdin.write(line.encode(charset))
                        p.stdin.close()
        allLines = []  # clear input buffer
    else:
        allLines.append(line)
        if line:
            allLinesContains = True
        print(line, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--inputfile", required=True, help="the JSON or YAML data input file"
    )
    parser.add_argument(
        "-t",
        "--templates",
        required=True,
        help="the templates to convert",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="the directory in which the results will be stored",
        default="",
    )

    args = parser.parse_args()
    input_full_path = os.path.abspath(args.inputfile)
    for template in args.templates:
        template_full_path = os.path.abspath(template)
        print(f"easygen {args.inputfile} {template_full_path}")
        executeAsCallback(
            ["easygen", template_full_path, input_full_path], "", args.directory, collectLines
        )
