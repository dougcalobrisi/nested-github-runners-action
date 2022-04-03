#!/bin/bash -ex
curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | grep "browser_download_url.*linux-x64-2.*.tar.gz" | grep -v noexternals | grep -v noruntime \
  | cut -d : -f 2,3 \
  | tr -d \" \
  | wget -O actions.tar.gz -i -

tar -zxf actions.tar.gz
rm -f actions.tar.gz
./bin/installdependencies.sh
mkdir /_work
