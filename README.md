# Experimental counterpart

Design materials for the experiment "Same Choices, Different Reasonings", a reservation-price design for selection neglect and elicitation effects. The experiment is the empirical counterpart of the companion preprint

Pinna, F. (2026). Dynamic Identification of Behavioral Reasoning in Finite Games. SSRN 7251718, version of August 8, 2026. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7251718

and it is anchored to that public version. The experiment is designed and documented for presentation within the course Experimental and Behavioural Economics at LUISS Guido Carli (Daniela Di Cagno and Irene Maria Buso). It has not been executed and no human data exist. This repository is provisional and will later become a section of the replication package of the preprint, https://github.com/francescopinna03/Dynamic_Identification.

## Layout

- `dossier/` the complete protocol, version 2.1 (`Protocol_dynamic_identification.md`), and its extracts: analysis plan, participant instructions, comprehension quiz and script, oral outline. It also holds the revision log, the layout files for the Word and PDF exports, and the five programs with their outputs in `design_data/` and `figures/`. `dossier/README.md` describes the package.
- `documents/` the design document (`Same_Choices_Design.tex`).
- `slides/` the first presentation deck (October 19, 2026) and the project update deck (November 4, 2026).
- `scripts/` the signed commit series used to update the repository.

## Reproducing the numbers

```
python3 -m pip install -r requirements.txt
cd dossier
python3 design_checks.py
python3 select_K_battery.py
python3 make_facsimile.py
python3 full_simulation.py all
```

`design_checks.py` reproduces the posterior enumeration, the price benchmarks, the anchoring counterexample and the analytic equivalence scenarios. `select_K_battery.py` selects the three games of the exploratory depth module. `make_facsimile.py` draws the illustrative task screen. `full_simulation.py` simulates the entire analysis procedure from the declared measurement model: type-one error and power of the first hypothesis, power of the equivalence test at each candidate sample size, the dyad bootstrap on an example dataset, the pilot rule, and the criteria of Section 12.3 of the protocol. Its parts can be run separately, `h1`, `h2`, `boot`, `figure`, `criteria`, with an optional replication count as second argument and, for `h1`, a scenario index as third argument. The certifying run uses the replication counts set at the top of the program, 2,000 for each simulation and 1,999 for the bootstrap. On an eight-core laptop each scenario of the first hypothesis takes about two hours, so the scenarios are best run one at a time and merged: The number of worker processes defaults to the number of cores and can be set with the environment variable `PROCESSES`. Random seeds are fixed, and results do not depend on the number of processes.

```
for i in 0 1 2 3 4; do python3 full_simulation.py h1 2000 $i; done
python3 -c "import csv,glob;r=[x for f in sorted(glob.glob('design_data/simulation_H1_*.csv')) for x in csv.DictReader(open(f))];w=csv.DictWriter(open('design_data/simulation_H1.csv','w',newline=''),fieldnames=list(r[0]));w.writeheader();w.writerows(r)"
python3 full_simulation.py h2
python3 full_simulation.py boot
python3 full_simulation.py figure
python3 full_simulation.py criteria
```

The outputs in `dossier/design_data/` come from the certifying run completed on October 31, 2026, documented in Section 12.4 of the protocol. The asymptotic likelihood-ratio test of the first hypothesis is mildly liberal at 100 subjects, so the program saves every replication in `replications_H1_*.csv` and calibrates the critical value by simulation (`calibrated_H1.csv`). With the calibrated value every criterion of Section 12.3 of the protocol is met, and the calibrated test is the primary test of the first hypothesis declared in Section 10.1.

## Citation

Pinna, F., and Sebastianelli, E. (2026). Same Choices, Different Reasonings: A Reservation-Price Design for Selection Neglect and Elicitation Effects. Course project, LUISS Guido Carli. https://github.com/francescopinna03/experimental_counterpart
