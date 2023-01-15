# The Markdown Crawler
The Markdown Crawler (MDC) is designed to 
* read recursively through directories and/or given files
* to find any markdown (*.md) files
* extract the object definitions out of it
* concats object properties which are distributed through several files
* resolves all object inheritance properties
* presents the result as json object string on stdout

The main propose of MDC is to collect data out of a tree of development documents written in Markdown to generate report documents out of it.

By that information about component properties can be generated and stored in a few central documents following the single source principle. All other downstreamed documents can then be made by automated report generators.


To save a majority of time by the handling of re-orcurring object properties like overall environment conditions, MDC allows to inherit properties from higher level "parent" documents. So such properties are need to maintained only once in a parent structure to inherit it to all children.


## What's MSON?

Markdown Syntax for Object Notation (MSON) is a plain-text syntax for the description and validation of data structures.
https://github.com/apiaryio/mson



## Dependencies
MDC uses the Markdown Renderer [Mistletoe](https://github.com/miyuchina/mistletoe), a Markdown Parser & Re- Renderer and supports its own renderer (`contrib/mson.py`) to translate the Markdown content.


That MSON Renderer implements today just its own small subset of the full MSON specification to  supply the features needed by MDC. 

## How it works



### Markdown lists as Object description

MDC uses the Markdown list notation to describe (nested) properties of 'something'. In the output of MDC this 'something' is representend as a nested hash of all its properties, identified by its 'name' property (in lower letters)

For simplicity, each Markdown file must contain only one object description. MDC identifies if a file contains an object description by searchin for a 'name' property in the root level like this:

document 1

    - name : requirement
    - environment
        - speed : 25

this would give a json object like

    {
        "requirement" : 
        {
            "name" : requirement"
            "environment" : 
            {
                "speed" : "25"
            }
        }
    }

Please note that actual also numbers are written as string

Now imagine we have a second file which exceeds the 'requirement' description

document 2

    - name : requirement
    - environment
        - min_temp : 30

this, together with document 1, would give the json object

    {
        "requirement" : 
        {
            "name" : requirement"
            "environment" : 
            {
                "speed" : "25",
                "min_temp" : "30"
            }
        }
    }

where the both 'environment' properties are joined.

In case the same property is given multiple times, its values are collected into an array like this

document 1

    - name : requirement
    - color : red


document 2

    - name : requirement
    - color : green

becomes

    {
        "requirement" : 
        {
            "name" : requirement" ,
            "color" : ["red" ,"green"]
        }
    }


### Inheritance

The 'parent' property is used to inherite all properties from another object

document 1

    - name : requirement
    - parent : requirement_parent
    - color : red


document 2

    - name : requirement_parent
    - min_temp : 20

becomes

    {
        "requirement" : 
        {
            "name" : requirement" ,
            "color" : ["red" ,"green"] ,
            "min_temp" : "20"

        }
    }

so childen can derive all the properties from their parents and grandparents without the need of list them all again by hand for each child.

To stop MDC from joining values from parents or siblings for a particular property, let its value start with '#' . If such a value starting with a '#' is found, it will not be combined with others. If the value is '#' only, it will be removed.


### Arrays instead of Hashes

By default a property in MDC is always a hash represented by its key and value.

But in some case like enumerations it's more convinient to have straight arrays of values without dedicated keys.

In MDC this is archived with the special key word 'item'. With that an array is written like a hash, but MSC converts this into an array. So

    - name : myModule
    - parent : requirement_par
    - requirements :
        - item 
            - text
                Lorem ipsum dolor sit amet, consetetur sadipscing elitr, 
                sed diam nonumy eirmod tempor invidunt ut labore et dolore
                magna aliquyam erat, sed diam voluptua. 
            - sev: 5
        - item 
            - text
                At vero eos et accusam et
                justo duo dolores et ea rebum. Stet clita kasd gubergren,
                no sea takimata sanctus est Lorem ipsum dolor sit amet. 
            - sev: 6


becomes

    {
        "myModule" : 
        {
            "name" : myModule" ,
            "requirements" : [
                {
                    "text" : "Lorem ipsum dolor sit amet, consetetur sadipscing elitr,\n
                    sed diam nonumy eirmod tempor invidunt ut labore et dolore\n
                    magna aliquyam erat, sed diam voluptua."] ,
                    "sev" : "5"
                },
                {
                    "text" : "At vero eos et accusam et\n
                    justo duo dolores et ea rebum. Stet clita kasd gubergren,\n
                    no sea takimata sanctus est Lorem ipsum dolor sit amet. "] ,
                    "sev" : "6"
                }
            ]
        }
    }

Multiline Strings: As visible in the example above, MDC can handle multiline strings, which is necessary to write paragraphs of a documentation. But because of todays parser limitations, these paragraphs must not contain blank lines in between.

### Tables as Hashes

Defining object properties as list is one way, but expecially in such cases with a lot of repeating properties MDC offers also the way to use tables as sources. MDC knows two kinds of tables, which differs only in the left-top-most cell, but give different results. At first we see a table, where the left- top-most -cell is not empty:

| key A   | key B   | key C   |
|---------|---------|---------|
| val 1 A | val 1 B | val 1 C | 
| val 2 A | val 2 B | val 2 C | 


MDC takes all header fields as key identiers and creates an array of objects with the given value for each key

    [
        {
            'key A' : 'val 1 A',
            'key B' : 'val 1 B',
            'key C' : 'val 1 C',
        },
        {
            'key A' : 'val 2 A',
            'key B' : 'val 2 B',
            'key C' : 'val 2 C',
        }
    ]

But in opposite here the left- top-most -cell is empty:

|          | key B   | key C   |
|----------|---------|---------|
| key 1    | val 1 B | val 1 C | 
| key 2    | val 2 B | val 2 C | 


In this case MDC takes all header fields as key identiers and creates an hash of objects, using the first column as object key identifier for the hash

    {
        'key 1' : {
            'key B' : 'val 1 B',
            'key C' : 'val 1 C',
        },
        'key 2' : {
            'key B' : 'val 2 B',
            'key C' : 'val 2 C',
        }
    }

## Ugly Problems
The parser is not perfect, so a few syntax rules has to be followed

a table header seperator has to have at least 3 '-' (='---') in a row

Correct:

  | --- |

Wrong:

  | -- |

## Post Processing the Result

As said, MDC generates a JSON object file which contains all found data. This file can be handled in many different ways. For convience we've made the helper tool jtp (JSON template processor), which transforms the json first into a flexible output format defined by an [EasyGen](https://github.com/go-easygen/easygen) template. If that output contains a special line
   #!# jtp #!# outputfilename #!# command to execute

then the output is written to a file and the command is started for further processing

Please see the [JTP Readme](JTP.md) for details