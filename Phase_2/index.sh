#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    echo "Syntax: ./index.sh <path_to_wiki_dump> <path_to_inverted_index> <stat_file_name>"
    exit 1
fi

echo "indexer.py running..."
python3 src/indexer.py $1 $2 $3