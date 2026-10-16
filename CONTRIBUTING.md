# Contributing

Corrections to broken links, transcription errors, and chapter-to-asset mappings are welcome. When reporting an issue, include the book chapter and listing, equation, or figure filename; for a code excerpt, include the surrounding passage or expected behavior. Keep publisher-facing asset filenames stable unless a change is coordinated with all references.

The printed snippets are pedagogical source assets rather than an installable package. The chapter 6 standalone script is executable reference code. If changing it, document any new environment requirement and add a focused check that proves the behavior. Do not commit credentials, local model weights, generated outputs, or third-party course material. Attribute external research and link to its primary source.

Run `bash scripts/check-assets.sh` after changing the asset inventory or navigation. The script checks inventory shape and the chapter 6 figure path documented here; it does not validate the semantics of the book's examples.

Run `python3 -m unittest discover -s tests -v` after changing the standalone script. The tests include an offline end-to-end loop and a mocked local-model protocol; they do not claim to reproduce the source course's benchmark results.
