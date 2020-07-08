# evo_path

> Evolves a shoreline simplification

[Someone asked](https://www.reddit.com/r/zekach/comments/hmkjx6/how_could_this_be_automated/)
how you could automatically simplify a shoreline. I got a bit very much into it.

## Table of Contents

- [Usage](#usage)
- [Performance](#performance)
- [TODOs](#todos)
- [NOTDOs](#notdos)
- [License](#license)
- [Contribute](#contribute)

## Usage

`./evolve.py [GREYSCALE_IMAGE [NUM_LINES]]`

An example run looks like this:

```
$ ./evolve.py
run_id = T1594228701825_R7b87828c
Success. Written to result_T1594228701825_R7b87828c_P10000.png and result_T1594228701825_R7b87828c_P10000.txt
```

FIXME: Show `ls` output, show results inline.

## Performance

FIXME

Probably terrible, although I'm not yet sure what the bottleneck is going to be: Drawing the polygon or evaluating the penalty amount?

## TODOs

* EVERYTHING

## NOTDOs

Here are some things this project will definitely not support:
* Disconnected landmasses
* Completely different approaches (do them as a final pass or something)

## License

All the code and documentation is MIT licensed.

The images are public domain, and are based on other public domain material ([Germany-Outline.svg, version 30 June 2010](https://commons.wikimedia.org/wiki/File:Germany-Outline.svg)).

There are many pieces of code with do "something something evolution something something image".
Hence I would like to tag this particular implementation like so:

### IRREGULAR RIDDANCE VIOLA

Please change this flavor identifier when redistributing modified versions.
The tag `"flavor": "IRREGULAR_RIDDANCE_VIOLA"` is also included into the output to identify output from this implementation. You could call it … flavor text! :D

If you want to reproduce this identifier, you can try getting inspired by running `shuf -n5 /usr/share/dict/american-english` on your system.

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/evo_path/issues/new) or submit PRs.
