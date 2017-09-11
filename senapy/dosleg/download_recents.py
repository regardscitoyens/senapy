import requests

from bs4 import BeautifulSoup

soup = BeautifulSoup(open('senat_list.html').read(), 'html5lib')
for link in soup.select('#main .box.box-type-02 .box-inner.gradient-01 a'):
    href = link.attrs['href']
    if '/dossier-legislatif/' in href:
        print(link.attrs['href'])
        print(link.text.strip())
        print()
        resp = requests.get('http://www.senat.fr' + link.attrs['href'])
        open('senat_dossiers/' + link.text.lower()[:100] + '.html', 'w').write(resp.text)