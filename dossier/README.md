# Experimental design materials

Design as of November 23, 2026. No experiment or pilot has been run.

- `Protocol_dynamic_identification.md` is the complete editable source.
- `Revision_log.md` records the decisions of each revision and their reasons.
- `Participant_instructions.md` contains only the instructions, written for the calendar with windows of 30 seconds.
- `Quiz_and_script.md` contains the solutions reserved for the experimenter.
- `Analysis_plan.md` contains the sections on hypotheses, dynamics, sample and the simulation of the analysis procedure.
- `design_checks.py` verifies the identities and generates posteriors, benchmark prices under the two rules, trial templates, calendars, the counterexample of the attraction toward the center and the TOST scenarios. The numbers quoted in the protocol are collected in `design_data/checks.json`.
- `partner_comparison_check.py` simulates the comparison between partners in the single-seller trials, with and without its correction. An optional argument sets the number of replications, 1,000 by default.
- `make_facsimile.py` draws the illustrative task screen.
- `full_simulation.py` simulates the entire analysis procedure for the design with two intensities and joint trials only and calibrates the critical value of the first hypothesis, in parts (`h1`, `h2`, `boot`, `figure`, `criteria`, `all`). The simulation of the present design is not yet included.
- `design_data/` contains reproducible CSV and JSON files.
- `figures/` contains the plot of predictions and power, the figure of the simulation and a facsimile of the task.
- `word_layout.py` applies the style to the DOCX produced by Pandoc, preserving native equations, and `layout.tex` is the LaTeX header for the PDF export.

The three extracts are cut from the corresponding sections of the protocol and are not edited by hand. The programs and the data files keep shorter names for some objects of the protocol, and Section 3 of the protocol lists the correspondence.

To reproduce the calculations use Python 3 with numpy, scipy and matplotlib, and run the programs in this directory. The certifying simulation takes about two hours per scenario of the first hypothesis on an eight-core laptop. The Markdown text can be converted to DOCX with Pandoc and then formatted with `word_layout.py`, or to PDF with Pandoc and `layout.tex`.

The package does not contain the course teaching materials, a ready collection app or an estimate of the SBB bridge. It contains the design and the declared checks. Before any execution, implementation, pilot and freezing according to the criterion preregistered in the dossier are required.
