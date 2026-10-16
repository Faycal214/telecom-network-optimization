# Data

## Starter instance

`examples/network.txt` is a lightly reformatted copy of the example SNDlib native-format network file published in the [official SNDlib input-format documentation](https://sndlib.put.poznan.pl/html/docu/io-formats/native/examples/network.txt). It contains 5 nodes, 8 undirected links and 3 OD demands.

The parser reads node names, link endpoints, preinstalled capacity, routing cost, module capacity/cost pairs, and demand volumes. It intentionally ignores comments, fixed-charge costs, hop limits, and admissible path restrictions. These assumptions are documented in `docs/mathematical_model.md`.

## Download the complete original SNDlib network archive

Download the native ASCII archive from:

https://sndlib.put.poznan.pl/download/sndlib-networks-native.tgz

Extract it locally and pass a network file to the experiment runner with `--instance PATH`. Do not commit the full archive unless redistribution rights and repository size have been checked; the project only needs the selected input file and the citation.

## Which benchmark representation is used?

The **original SNDlib native data** is the primary input because we are formulating our own model in Pyomo. The **SNDlib-MIPs** MPS collection is an alternative benchmark of pre-formulated optimization models, with formulation differences from the primary paper; it is not used in the starter experiment.
