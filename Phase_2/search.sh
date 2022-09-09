#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    echo "Syntax: ./search.sh <path_to_inverted_index> <query_file_path / query_string>"
    exit 1
fi

echo "search.py running..."
python3 src/search.py $1 $2 False