#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    echo "Syntax: run.sh <path_to_wiki_dump> <size_of_wiki_dump(in_GB)>"
    exit 1
fi

echo "Trimming data..."
python3 src/trim.py $1 $2