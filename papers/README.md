# Research references

## Primary paper

Raack, C., Koster, A. M. C. A., Orlowski, S., & Wessely, R. (2007). **Capacitated network design using general flow-cutset inequalities.**

- [Paper PDF (Optimization Online)](https://optimization-online.org/wp-content/uploads/2006/11/1525.pdf)
- The paper develops MIR-based flow-cutset inequalities for directed, bidirected, and undirected capacitated network-design formulations and evaluates separation routines on 54 SNDlib model instances.

## Benchmark data

- **SNDlib networks and default traffic matrices:** https://sndlib.put.poznan.pl/networks.overview.action
- **SNDlib native ASCII archive:** https://sndlib.put.poznan.pl/download/sndlib-networks-native.tgz
- **SNDlib input-format documentation:** https://sndlib.put.poznan.pl/html/docu/io-formats/index.html
- **The native-format example used as the starter instance:** https://sndlib.put.poznan.pl/html/docu/io-formats/native/examples/network.txt
- **Alternative pre-formulated MILP set (not used as the primary input here):** https://doi.org/10.5281/zenodo.8021237

The SNDlib-MIPs set contains 289 MILP files derived from SNDlib but uses some formulation choices different from the formulations used in the primary paper. It is therefore not treated as a drop-in replacement for the original SNDlib data in this prototype.
