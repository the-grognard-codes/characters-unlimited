"""Rebuild HU2 physical-size and height/weight charts from rendered PDF 167."""
import re
from repair_source_passages import ROOT, load, replace, save_repairs


def markdown(headers, rows):
    assert all(len(row)==len(headers) for row in rows)
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',
        *('| '+' | '.join(map(str,row))+' |' for row in rows)])


def main():
    name='Heroes Unlimited - RPG - 2E.md'
    weights=['0–1 lbs',*[f'To {n:,} lbs' for n in [5,10,20,40,75,100,150,175,200,250,300,350,400,500,600,800,1000,1500,2500]]]
    iq=['-8','-6','-4','-2']+['—']*16
    ps=['-12','-6','-3','-2','-1','0']+[f'+{i}' for i in range(1,15)]
    pe=['-4','-2','-1']+['0']*5+[f'+{i}' for i in range(1,13)]
    speed=['+7','+5','+3']+['0']*7+[str(-i) for i in range(1,11)]
    sdc=[5,10,15,20,25,30,30,35,35,35,40,40,45,50,55,60,65,70,75,80]
    rows=[[i+1,weights[i],i*5,iq[i],ps[i],pe[i],speed[i],sdc[i]] for i in range(20)]
    text=markdown(['Growth Steps','Weight','BIO-E','I.Q.','P.S.','P.E.','Spd.','SDC'],rows)
    tables=list(re.finditer(r'(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+',load(name)))
    old=[m.group().rstrip('\n') for m in tables if 'Growth Steps Growth Steps' in m.group()];assert len(old)==1
    replace(name,old[0],text,167,166,'Rebuilt 20-row physical size chart; visually checked all 160 cells, corrected duplicated values, sign errors and displaced columns')
    values='''3D6 ounces|1D6|2D6|3D6
1D6 pounds|3D6|12+1D6|12+2D6
4+1D6 pounds|12+1D6|12+2D6|12+3D6
10+2D6 pounds|12+3D6|24+2D6|24+3D6
20+4D6 pounds|24+1D6|36+2D6|36+3D6
40+6D6 pounds|24+2D6|48+1D6|48+3D6
75+3D10 pounds|24+3D6|60+1D6|60+2D6
100+6D10 pounds|36+1D6|60+1D6|60+3D6
150+3D10 pounds|36+2D6|60+2D6|72+2D6
175+3D10 pounds|36+3D6|60+3D6|72+3D6
200+6D10 pounds|48+1D6|72+1D6|84+2D6
250+6D10 pounds|48+2D6|72+2D6|84+3D6
300+6D10 pounds|48+3D6|72+3D6|96+2D6
350+6D10 pounds|60+1D6|84+1D6|96+3D6
400+1D% pounds|60+2D6|84+2D6|108+2D6
500+1D% pounds|60+3D6|84+3D6|108+3D6
600+2D% pounds|72+1D6|96+1D6|120+2D6
800+2D% pounds|72+2D6|96+2D6|120+3D6
1,000+5D% pounds|72+3D6|96+3D6|132+2D6
1,500+(% × 100)|72+4D6|132+3D6|'''
    rows=[]
    for i,line in enumerate(values.splitlines(),1):
        weight,*heights=line.split('|');rows.append([i,weight,*[v+' inches' if v else '' for v in heights]])
    text=markdown(['Size','Weight','Height—Short','Height—Medium','Long'],rows)
    old=[m.group().rstrip('\n') for m in re.finditer(r'(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+',load(name)) if 'Height—Short' in m.group()];assert len(old)==1
    replace(name,old[0],text,167,166,'Rebuilt 20-row height and weight chart; visually checked all 100 cells, restored row 7 and corrected plus/minus/dice errors. Size 20 Long is blank in source and retained blank.')
    old=[m.group().rstrip('\n') for m in re.finditer(r'(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+',load(name)) if 'Average Human Kick Attack' in m.group()];assert len(old)==1
    text=markdown(['Foot strike','Damage'],[['Average Human Kick Attack','2D4'],['Karate Kick Attack','2D6'],['Jump Kick','3D6×2'],['Roundhouse Kick','3D6'],['Snap Kick','1D6'],['Wheel Kick','2D6'],['Knee','1D6']])
    replace(name,old[0],text,69,68,'Rebuilt collapsed two-column Foot Strikes list as a seven-row table; visually checked all entries')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-21.json')


if __name__=='__main__':main()
