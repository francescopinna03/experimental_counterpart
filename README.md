# Experimental counterpart

Design materials for the experiment "Same Choices, Different Reasonings", a reservation-price design for selection neglect and elicitation effects. The experiment is the empirical counterpart of the companion preprint

Pinna, F. (2026). Dynamic Identification of Behavioral Reasoning in Finite Games. SSRN 7251718, version of August 8, 2026. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7251718

and it is anchored to that public version. The experiment is designed and documented for presentation within the course Experimental and Behavioural Economics at LUISS Guido Carli (Daniela Di Cagno and Irene Maria Buso). It has not been executed and no human data exist. This repository is provisional and will later become a section of the replication package of the preprint, https://github.com/francescopinna03/Dynamic_Identification.

## Layout

- `dossier/` the complete protocol in Italian (`Protocollo_identificazione_dinamica.md`), participant instructions, comprehension quiz and script, analysis plan, oral outline, revision log, the Word layout files, and the three verification programs with their outputs in `dati_disegno/` and `figure/`. `LEGGIMI.md` describes the package.
- `documents/` the English design document (`Same_Choices_Design.tex`) and the Italian orientation note for the co-author.
- `slides/` the first presentation deck (October 19, 2026) and the project update deck (November 4, 2026).
- `scripts/` the signed commit series used to populate the repository.

## Reproducing the numbers

```
python3 -m pip install -r requirements.txt
cd dossier
python3 verifica_disegno_v2.py
python3 seleziona_batteria_K.py
python3 simulazione_completa.py tutto
```

`verifica_disegno_v2.py` reproduces the posterior enumeration, the price benchmarks, the anchoring counterexample and the analytic equivalence scenarios. `seleziona_batteria_K.py` selects the three games of the exploratory depth module. `simulazione_completa.py` simulates the entire analysis procedure from the declared measurement model: type-one error and power of the first hypothesis, power of the equivalence test at each candidate sample size, the dyad bootstrap on an example dataset, the pilot rule, and the criteria of Section 12.3 of the protocol. Its parts can be run separately, `h1`, `h2`, `boot`, `figura`, `criteri`, with an optional replication count as second argument and, for `h1`, a scenario index as third argument. The certifying run uses the replication counts set at the top of the program, 2,000 for each simulation and 1,999 for the bootstrap, and takes several hours on a multicore machine. The number of worker processes defaults to the number of cores and can be set with the environment variable `PROCESSI`. Random seeds are fixed, and results do not depend on the number of processes.

The files currently in `dossier/dati_disegno/` named `simulazione_*.csv` and `bootstrap_H1_esempio.csv` come from the design-check run of October 28, 2026, with reduced replication counts, five quadrature nodes per dimension and zero error correlation between the two lists, as documented in Section 12.4 of the protocol. The certifying run replaces them.

## Citation

Pinna, F., and Sebastianelli, E. (2026). Same Choices, Different Reasonings: A Reservation-Price Design for Selection Neglect and Elicitation Effects. Course project, LUISS Guido Carli. https://github.com/francescopinna03/experimental_counterpart
