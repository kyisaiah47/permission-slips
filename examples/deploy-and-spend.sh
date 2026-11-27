#!/bin/sh
# An until-spent slip lasts through failed builds and retries. Your own script ends it,
# after the thing it unlocked has actually worked.
set -eu
target="$1"
./scripts/deploy.sh "$target"
curl -fsS "https://$target.example.com/health" >/dev/null   # verify it is live
python3 ~/.permission-slips/slip.py spend deploy "$target"
