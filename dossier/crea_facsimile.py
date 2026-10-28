"""Schermata illustrativa esatta del compito X, non applicazione di raccolta."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

out=Path(__file__).resolve().parent/'figure'/'facsimile_X.png'
fig,ax=plt.subplots(figsize=(11.2,7.0));fig.patch.set_facecolor('#F3F5F6')
ax.set(xlim=(0,112),ylim=(0,70));ax.axis('off')
def box(x,y,w,h,fill='#FFFFFF',edge='#D3DBDF'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.3,rounding_size=1',
        facecolor=fill,edgecolor=edge,lw=1))
def txt(x,y,s,size=11,color='#24363D',weight='normal',**kw):
    ax.text(x,y,s,fontsize=size,fontfamily='DejaVu Sans',color=color,fontweight=weight,va='top',**kw)
txt(4,67,'Decisione di acquisto',20,weight='bold')
txt(4,61,'Il bene vale 30 oppure 90 punti. Probabilità iniziale del valore 90: 40%.',11)
box(4,49,104,8,'#E9EFF2')
txt(7,55,'Informazioni disponibili',10,weight='bold')
txt(7,52,'I certificati non sono ancora arrivati. Le due liste riguardano lo stesso bene.',10)
for x,title,rule in [(4,'Venditore sempre disponibile','È sempre disponibile.'),
                     (58,'Venditore selettivo','Disponibile nell’80% dei casi se vale 30\ne nel 20% dei casi se vale 90.')]:
    box(x,12,50,33)
    txt(x+3,42,title,12,weight='bold')
    txt(x+3,37,rule,10)
    txt(x+3,29,'Acquisto per prezzi fino a',10)
    box(x+34,24,12,5,'#F7F9FA')
    txt(x+36,28,'___',12)
    txt(x+3,22,'Prezzi ammessi: da 20 a 90, passo 1.',9)
    txt(x+3,18,'Oppure: rinuncio a tutti / acquisto a tutti.',9)
txt(5,9,'Prima di confermare vedrai il riepilogo degli acquisti e delle rinunce.',10)
txt(5,5,'Se la lista viene estratta, il prezzo è sorteggiato. Non è automaticamente la tua soglia.',9)
fig.subplots_adjust(0,0,1,1);fig.savefig(out,dpi=160)
print(out)
