# Decisioni della revisione 2

9 ottobre 2026. Disegno progettato, non eseguito.

La versione 2 sostituisce il protocollo 1.1. Il nucleo confermativo è il modulo X in prezzi. Profondità e ponte rimangono esplorativi.

| Proposta | Decisione | Motivo |
|:--|:--|:--|
| Certificati al 60% e 70% | Adottata | L'audit conferma 3,40 prove discriminanti contro 1,05 nel vecchio compito binario |
| Eliminazione della scoring rule e del calcolatore | Adottata | Il problema di incentivi comportamentali documentato da Danz e coautori è pertinente |
| Due prezzi per separare posterior e selezione | Adottata con ipotesi esplicite | Il benchmark condizionato deve essere costruito dal posterior implicato dal primo prezzo |
| Rapporto individuale esatto da liste a passi di cinque | Corretto | Le liste danno intervalli; l'errore nei due prezzi rende il rapporto non lineare e distorto |
| Griglia dei prezzi | Passo uno; formati 20-90 e 30-100 | Stessa lunghezza e prezzi economici comuni, centri diversi per verificare l'ancoraggio |
| Due intensità come controllo sufficiente | Ridimensionato | Il 10% di attrazione verso 57,5 genera contrazioni apparenti 0,1098 e 0,1072 |
| Calibrazione | Otto prove a valore certo oltre alle sedici urne | Le urne non controllano un errore specifico dello strumento in prezzi |
| Slot inattivo pagato tramite la finale | Non adottata | Con tre slot equiprobabili la finale pesa 1, 2/3 e 1/3 in F, S e R |
| Slot inattivo | Riserva al 50% | Equivale a una politica sempre disponibile e conserva il pagamento delle decisioni comuni |
| Assenza di rischio monetario | Premio binario mantenuto | Con pagamenti monetari diretti il prezzo di riserva dipenderebbe dalle preferenze per il rischio |
| 11-20 nel nucleo K con separazione di due passi | Escluso dal nucleo | Livelli adiacenti ed equilibrio misto non soddisfano il vincolo |
| Batteria K | Tre giochi selezionati, sei prove con scambio dei ruoli | Criterio maximin dell'informazione efficiente su un benchmark esplicito |
| Liste di probabilità equivalente | Mantenute con controllo di complementarità | Sono sensibili anche alle preferenze per la fonte dell'incertezza |
| Sedici urne come limite superiore al rumore | Affermazione rimossa | La precisione non si trasferisce automaticamente fra compiti |
| Identità di variazione come test sui prezzi grezzi | Corretta per il modello di misura | Con rumore indipendente lo scarto spurio vale tre varianze dell'errore |
| Campione da 300 | Base condizionata al criterio del pilota | Per l'80% di potenza TOST nello scenario centrale serve SD circa 5,92 o inferiore |
| χ ricavato dalle soglie | Denominato contrazione effettiva ψ | Coincide con χ nella restrizione statica, non automaticamente nel ponte dinamico |

Le due primarie sono la contrazione effettiva media in S e l'equivalenza media F-R del prezzo finale osservabile entro tre punti. La specificazione di H1 include censura e modello di misura. La simulazione completa di recupero, errore di primo tipo e potenza è una condizione prima dell'eventuale esecuzione, non un risultato già ottenuto.

Le verifiche consegnate sono riproducibili con verifica_disegno_v2.py e seleziona_batteria_K.py. Il protocollo contiene istruzioni, quiz, calendario, pagamenti, piano di analisi, budget e una traccia di sette diapositive.

## Aggiornamento del 15 ottobre 2026

L'esperimento del corso è ancorato alla versione pubblica del preprint, SSRN 7251718, 8 agosto 2026. La voce bibliografica del Protocollo sostituisce il riferimento al file con la citazione SSRN e indica gli ancoraggi esatti, la sezione 4.2 con le Proposizioni 4.2 e 4.3 per la trasformazione della congiunta, il Teorema 9.1 per l'osservazione dei processi, la (77) e la sezione 13.1 per l'informazione efficiente. La Motivazione dichiara il disegno attuazione delle misure chieste dalle sezioni 10.3 e 12.4 e dalle conclusioni del preprint e lo distingue dalla batteria dei tre giochi della sezione 12. I riferimenti di lavorazione nel testo sono stati sostituiti con citazioni complete. L'addendum del 13 ottobre e i ritocchi derivati dalla revisione del paper restano fuori dal percorso del corso e rientrano soltanto con il caricamento della revisione su SSRN. Numeri, tabelle e programmi sono invariati.

## Aggiornamento del 28 ottobre 2026

Aggiunta la sezione 12.4 con la simulazione completa della procedura di analisi dal modello di misura dichiarato, programma simulazione_completa.py e figura simulazione_completa.png. La tabella della 12.2 è qualificata come calcolo analitico. La corsa riportata è una verifica di progetto a repliche ridotte, la corsa certificante della 12.3 resta prevista al momento del pilota. La regola di pagamento della sezione 9 e il budget della sezione 14 sono invariati e già completi. Il programma di simulazione è portato alla versione definitiva, con correlazione dell'errore fra le liste, esecuzione parallela e parte criteri, e il materiale è pubblicato nel repository experimental_counterpart.
