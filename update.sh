#!/bin/bash

#set -o xtrace
set -o errexit

pipenv run python ./script.py|tee stats.csv && {
    hash dos2unix 2>/dev/null && {
	dos2unix -k -n stats.csv{,.new} && mv -f stats.csv{.new,}
    } ||:
    pipenv run jupyter nbconvert --to notebook --inplace --execute Plots.ipynb
}
