# Wrapper to invoke Python release publisher
$ErrorActionPreference = "Stop"
py -3.12 scripts\publish_release.py $args
