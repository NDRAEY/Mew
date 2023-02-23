#!/bin/bash

set -e  # exit on error

PROJECT="mew_pl/__main__.py"

for i in examples/*; do \
	echo "=====================" $i "====================="
	python3 $PROJECT $i
done;


echo 
echo 
echo 
echo -e "\033[32;1mALL COMPILATION TESTS DONE!!!\033[0m"
echo
echo
echo
