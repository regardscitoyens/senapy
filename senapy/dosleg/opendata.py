import csv

from lawfactory_utils.urls import download


def fetch_csv():
    csv_resp = download("http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv").text
    return list(csv.DictReader(csv_resp.split('\n'), delimiter=';'))
