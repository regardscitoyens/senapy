import json, sys

from ._compare_outputs import gen_comparator


def compare(proc, me, verbose=True):
    scores = {'ok': 0, 'nok': 0}

    myprint = print
    if not verbose:
        myprint = lambda *args: None

    test = gen_comparator(proc, me, scores, print=myprint)
    test('url_an', 'url_dossier_assemblee')
    test('url_senat', 'senat_url')
    test('legislature', 'assemblee_legislature')
    test('legislature')
    test('id_an', 'assemblee_id')

    myprint('NOK:', scores['nok'])
    myprint('OK:', scores['ok'])

    return scores['nok'], scores['ok']

if __name__ == '__main__':
    proc = json.load(open(sys.argv[1]))
    me = json.load(open(sys.argv[2]))
    compare(proc, me)
