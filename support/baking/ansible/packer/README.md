# To update a packer template

Make sure you have [packer](http://packer.io) installed.

Make sure you have an [atlas](http://atlas.hashicorp.com) account

then using your atlas token:

`export ATLAS_TOKEN="<token>"`

`packer push -name='<account>/<build name>' <template name>.json`

e.g.

`packer push -name='knservis/elk' elk.json`
