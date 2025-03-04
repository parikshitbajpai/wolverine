#!/bin/bash
for ((i=573; i<=2273; i+=10))
do
    echo -e "\ns-c n=1, p=1e5, x(cr)=0.01 t=$i \nc-e \ns-a-v 1 x(cr) 0 1 0.01 \nstep \nsep \npost \nenter table \nT$i\nx(cr), g(fcc), g(bcc), g(liquid), m(fcc,cr), m(fcc,ni), m(bcc,cr), m(bcc,ni), m(liquid,cr), m(liquid,ni), mu(cr), mu(ni), mur(cr,fcc), mur(ni,fcc), mur(cr,bcc), mur(ni,bcc), mur(cr,liquid), mur(ni,liquid); \n \ntabulate \nT$i \nT$i.dat \nback \nr-m \n" >> calcNiCr.TCM
done