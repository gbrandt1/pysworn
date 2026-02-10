#!/bin/bash
gitrepo=git+https://github.com/gbrandt1/datasworn.git
j=datasworn
subdir=pkg/python/$j/src/$j

for i in core classic delve lodestar starforged sundered_isles
do
	uv add "$gitrepo/#egg=$j-$i&subdirectory=$subdir/$i"
done

j=datasworn-community-content
subdirc=pkg/python/$j/src/${j//-/_}
for i in ancient-wonders fe-runners ironsmith starsmith
do	
	uv add "$gitrepo/#egg=$j-$i&subdirectory=$subdirc/$i"
done
