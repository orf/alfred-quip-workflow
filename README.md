# Alfred Quip Workflow

Search documents in Quip from within Alfred! Alfred 3 only

## Install

Grab the workflow from one of the latest Github releases, or from Packal: http://www.packal.org/workflow/quip

Run `set-quip-key` to open the Quip page, sign in and get your key.

Then run `set-quip-key [KEY HERE]` to add the key.

## Usage

Quip does not have a search API, so this workflow will create a local cache of your documents that is
refreshed in the background every hour. Just type `quip [search term]` and you will see a list of documents.
