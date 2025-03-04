#!/bin/bash
for ((i=573; i<=2273; i+=10))
do
    echo -e "\ns-c n=1, p=1e5, x(cr)=0.01 t=$i \nc-e \ns-a-v 1 x(cr) 0 1 0.01 \nstep \nsep \npost \nenter table \nT$i\nx(cr), g(fcc), g(bcc), g(liquid), m(fcc,cr), m(fcc,fe), m(bcc,cr), m(bcc,fe), m(liquid,cr), m(liquid,fe), mu(cr), mu(fe), mur(cr,fcc), mur(fe,fcc), mur(cr,bcc), mur(fe,bcc), mur(cr,liquid), mur(fe,liquid); \n \ntabulate \nT$i \nT$i.dat \nback \nr-m \n" >> calcFeCr.TCM
done