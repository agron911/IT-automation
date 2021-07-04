#!/bin/bash

for file in *.html;do
    name=$(basename "$file" .html)
    sleep 1
    mv "$file" "$name.HTM"
done