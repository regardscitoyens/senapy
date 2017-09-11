import sys, os

import requests
from bs4 import BeautifulSoup
from slugify import slugify

dest = sys.argv[1] if len(sys.argv) > 1 else 'senat_dossiers/'
print('saving to', dest)

if not os.path.exists(dest):
    os.makedirs(dest)

html = requests.get('http://www.senat.fr/dossiers-legislatifs/textes-recents.html').text
soup = BeautifulSoup(html, 'html5lib')

for link in soup.select('#main .box.box-type-02 .box-inner.gradient-01 a'):
    href = link.attrs['href']
    if '/dossier-legislatif/' in href:
        print(link.attrs['href'])
        print(link.text.strip())
        print()
        resp = requests.get('http://www.senat.fr' + link.attrs['href'])
        open(dest + slugify(link.attrs['href']) + '.html', 'w').write(resp.text)