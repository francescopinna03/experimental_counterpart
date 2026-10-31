"""Exact illustrative screen of task X, not a collection application."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

out=Path(__file__).resolve().parent/'figures'/'facsimile_X.png'
fig,ax=plt.subplots(figsize=(11.2,7.0));fig.patch.set_facecolor('#F3F5F6')
ax.set(xlim=(0,112),ylim=(0,70));ax.axis('off')
def box(x,y,w,h,fill='#FFFFFF',edge='#D3DBDF'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.3,rounding_size=1',
        facecolor=fill,edgecolor=edge,lw=1))
def txt(x,y,s,size=11,color='#24363D',weight='normal',**kw):
    ax.text(x,y,s,fontsize=size,fontfamily='DejaVu Sans',color=color,fontweight=weight,va='top',**kw)
txt(4,67,'Purchase decision',20,weight='bold')
txt(4,61,'The good is worth 30 or 90 points. Initial probability of value 90: 40%.',11)
box(4,49,104,8,'#E9EFF2')
txt(7,55,'Available information',10,weight='bold')
txt(7,52,'The certificates have not arrived yet. Both lists refer to the same good.',10)
for x,title,rule in [(4,'Always-available seller','Always available.'),
                     (58,'Selective seller','Available 80% of the time if worth 30\nand 20% of the time if worth 90.')]:
    box(x,12,50,33)
    txt(x+3,42,title,12,weight='bold')
    txt(x+3,37,rule,10)
    txt(x+3,29,'I buy at prices up to',10)
    box(x+34,24,12,5,'#F7F9FA')
    txt(x+36,28,'___',12)
    txt(x+3,22,'Allowed prices: 20 to 90, step 1.',9)
    txt(x+3,18,'Or: decline at all prices / buy at all prices.',9)
txt(5,9,'Before confirming you will see the summary of purchases and refusals.',10)
txt(5,5,'If the list is drawn, the price is drawn at random. It is not automatically your threshold.',9)
fig.subplots_adjust(0,0,1,1);fig.savefig(out,dpi=160)
print(out)
