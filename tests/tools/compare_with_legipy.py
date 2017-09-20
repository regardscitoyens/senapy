import json, sys

def compare(proc, me, verbose=True):
    score_ok = 0
    score_nok = 0

    myprint = print
    if not verbose:
        myprint = lambda *args: None

    # i like to write cryptic function sometimes also
    def test_test(proc, me):
        def test(a, b=None, a_key=lambda a: a):
            nonlocal score_nok, score_ok
            if b is None:
                b = a
            a_val = a_key(proc.get(a))
            b_val = me.get(b)
            if a_val != b_val:
                print('!! NOK !!', a,' diff:', a_val, 'VS', b_val)
                score_nok += 1
            else:
                print('OK', a, '(', a_val, ')')
                score_ok += 1
        return test

    test = test_test(proc, me)
    test('url_an', 'url_dossier_assemblee')
    test('url_senat', 'senat_url')
    test('legislature', 'assemblee_legislature')
    test('legislature')
    test('id_an', 'assemblee_id')

    myprint('NOK:', score_nok)
    myprint('OK:', score_ok)
    return score_nok, score_ok

if __name__ == '__main__':
    proc = json.load(open(sys.argv[1]))
    me = json.load(open(sys.argv[2]))
    compare(proc, me)
