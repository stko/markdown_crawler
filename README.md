# The Markdown Crawler
The Markdown Crawler (MDC) was made to 
* read recursively through directories
* find any markdown (*.md) files
* extract the MSON object definitions out of it
* resolves all object inheritance properties

The main propose of MDC is to inherit properties from higher system definitions down to smaller single object  out of a tree of development documents written in Markdown to generate development documents out of it.


## What's MSON?

Markdown Syntax for Object Notation (MSON) is a plain-text syntax for the description and validation of data structures.
https://github.com/apiaryio/mson


## Dependencies
MDC uses the Markdown -> MSON Renderer, available as a [fork](https://github.com/stko/mistletoe) from Mistletoe, a Markdown Parser & Re- Renderer