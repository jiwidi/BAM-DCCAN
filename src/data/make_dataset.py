# -*- coding: utf-8 -*-
from __future__ import division
import click
import logging
import pandas as pd 
import numpy as np 
import requests
import os

import sys
from multiprocessing import Pool
import sqlite3
from pathlib import Path
from dotenv import find_dotenv, load_dotenv


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('Downloading images from sqlite database to /data/interim/<category>')

    #Establish connection with our database
    database = sqlite3.connect('../../data/raw/20170509-bam-2.2m-Nja9G.sqlite') #connected to database with out error
    #We query the database
    dfSOURCE = pd.read_sql_query("SELECT * FROM modules", database)
    dfSCORES = pd.read_sql_query("SELECT * FROM scores", database)
    #Categorial values we will store, paintType emotion and content
    paintType=['media_oilpaint','media_3d_graphics','media_pen_ink','media_comic'
           ,'media_vectorart','media_graphite','media_watercolor']

    emotion=['emotion_gloomy','emotion_happy','emotion_peaceful','emotion_scary']
    content=['content_bicycle','content_bird','content_building','content_cars','content_cat','content_dog','content_flower','content_people','content_tree']

    #Store the categorical value that defines each img

    dfSCORES['paintType']=dfSCORES[paintType].idxmax(axis=1)
    dfSCORES['emotion']=dfSCORES[emotion].idxmax(axis=1)
    dfSCORES['content']=dfSCORES[content].idxmax(axis=1)

    dfSCORES['TOPpaintType']= dfSCORES[paintType].max(axis=1)
    dfSCORES['TOPemotion']=dfSCORES[emotion].max(axis=1)
    dfSCORES['TOPcontent']=dfSCORES[content].max(axis=1)


    listC=['mid','paintType','emotion','content','TOPcontent','TOPemotion','TOPpaintType']
    global df
    df=pd.merge(dfSOURCE, dfSCORES[listC], on =['mid'])

    #Download all images


    for type in paintType:
        path = "../../data/interim/"+type
        if not os.path.exists(path):
            os.mkdir(path)
            logger.info('Creating path: {0}'.format(path))
   
    pool = Pool()
    for i, _ in enumerate(pool.imap(downloadFromSrc, range(len(df))), 1):
        sys.stderr.write('\r Downloading images, done {0:%}'.format(i/len(df)))
    pool.map(downloadFromSrc, range(len(df)))  



def downloadFromSrc(u):
    """Code for donwloading a image, recieves a row from the dataset

    """
    row = df.loc[u]
    imgClass = row['paintType'] + '/'
    url = row['src']
    filename = "../../data/interim/"+imgClass+str(u)+'.jpg'
    result = requests.get(url, stream=True)
    if result.status_code == 200:
        path = "../../data/interim/"+imgClass
        if not os.path.exists(path):
            os.mkdir(path)
        image = result.raw.read()
        open(filename,"wb").write(image)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
