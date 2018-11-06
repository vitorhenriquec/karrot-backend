#!/bin/sh

function mod() {
  from=$1
  to=$2
  dir=${3:-"foodsaving config grafana"}
  for d in $dir; do
    echo codemod -m --accept-all -d $d --extensions py,po,json,mjml "$from" "$to"
    codemod -m --accept-all -d $d --extensions py,po,json,mjml "$from" "$to"
  done
}

if [ -d foodsaving/stores ]; then
  if [ -d foodsaving/places ]; then
    echo "Oops foodsaving/places already exists, please remove it!"
    exit 1
  fi
  mv foodsaving/stores foodsaving/places
fi

for f in $(find foodsaving/*/migrations/*.py | grep store); do
  fnew=$(echo $f | sed 's/_store_/_place_/g')
  mv "$f" "$fnew"
done

mod '_store_' '_place_'
mod '_stores_' '_places_'
mod '\bstore_' 'place_'
mod '_store\b' '_place'
mod '_stores\b' '_places'
mod '\bStore\b' 'Place'
mod '([a-z])Store([A-Z])' '\1Place\2'
mod '([a-z])Store\b' '\1Place'
mod '\bStore([A-Z])' 'Place\1'
mod '([a-z])Stores([A-Z])' '\1Places\2'
mod '\bStores([A-Z])' 'Places\1'
mod '([a-z])Stores\b' '\1Places'
mod '\bstore\b' 'place'
mod '\bstore2\b' 'place2'
mod '\bstores\b' 'places'
mod '\bStores\b' 'Places'

mod 'place_true' 'store_true' foodsaving/management/commands
