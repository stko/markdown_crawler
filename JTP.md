# JTP JSON Template Processor

As said, MDC generates a JSON object file which contains all found data. This file can be handled in many different ways. For convience we've made the helper tool jtp (JSON template processor), which transforms the json first into a flexible output format defined by an [EasyGen](https://github.com/go-easygen/easygen) template. If that output contains a special line

    #!# jtp #!# outputfilename #!# command to execute

then the output is written to a file and the command is started for further processing

## EasyGen
[EasyGen](https://github.com/go-easygen/easygen) is a quite good tool to fill templates with data coming out of JSON or Yaml files, but EasyGen can neither split a single data source into multiple output file nor it can start any further processing.

## JTP
That is where jtp comes in place to split or further process the generated outputs

The command line usage of `jtp.py` already explains it all:

    >python jtp.py
    usage: jtp.py [-h] -i INPUTFILE -t TEMPLATES [TEMPLATES ...]
    

Jtp forwards the input data and each template file one by one to easygen. Easygen then transforms each template into its output, which is then received by jtp again. If that output does contain the line

    #!# jtp #!# outputfilename #!# command to execute

then jtp writes all the output which is has received so far into the file `outputfilename` and starts the `command to execute`. If the `outputfilename` is "`-`", then the text is not stored as a file, but given as stdin to the `command to execute`.

If `command to execute` is "`-`", then the data is only written to `outputfilename`, but no `command to execute` is raised