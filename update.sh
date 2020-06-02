#!/bin/bash

#set -o xtrace
set -o errexit

pipenv run python ./script.py|tee stats.csv &&
  pipenv run jupyter nbconvert --to notebook --inplace --execute Plots.ipynb
