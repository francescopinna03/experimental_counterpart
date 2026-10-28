# Materiali del disegno sperimentale

Versione 2.0, 9 ottobre 2026. Sostituisce la versione 1.1. Nessun esperimento o pilota è stato eseguito.

- Protocollo_identificazione_dinamica.md è la fonte completa modificabile.
- Revisioni_2_0.md riporta le decisioni e i motivi della revisione.
- Istruzioni_partecipanti.md contiene soltanto le istruzioni da adattare per ciascun protocollo prima dell'implementazione.
- Quiz_e_copione.md contiene le soluzioni riservate al conduttore.
- Piano_analisi.md contiene le sezioni su ipotesi, dinamica, campione e dati.
- Traccia_presentazione.md contiene la traccia delle sette diapositive, con il nuovo esempio in prezzi.
- verifica_disegno_v2.py verifica le identità e genera posterior, template, controesempio di ancoraggio e scenari TOST.
- seleziona_batteria_K.py seleziona tre giochi e produce le diagnostiche Fisher del benchmark ricorsivo.
- simulazione_completa.py simula l'intera procedura di analisi dal modello di misura dichiarato, con errore di primo tipo, potenza di H1 e H2, bootstrap di esempio e regola del pilota, a parti (h1, h2, boot, figura).
- dati_disegno contiene CSV e JSON riproducibili.
- figure contiene il grafico di predizioni e potenza e un facsimile del compito.
- impagina_word.py applica lo stile al DOCX prodotto da Pandoc, preservando le equazioni native.

Per riprodurre i calcoli usare Python 3 con numpy, scipy e matplotlib. Eseguire i programmi nella directory dei materiali. La simulazione completa con le repliche certificanti richiede ore su un solo core. Il PDF consegnato è l'esportazione verificata della versione Word. Il testo Markdown può essere convertito in DOCX con Pandoc e poi formattato con impagina_word.py.

Il pacchetto non contiene i materiali didattici del corso, un'app pronta per la raccolta o una stima del ponte SBB. Contiene il disegno e le verifiche dichiarate. Prima di un'eventuale esecuzione sono necessari implementazione, pilota e congelamento secondo il criterio preregistrato nel fascicolo.
