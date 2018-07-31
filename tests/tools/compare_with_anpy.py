import json, sys

# quick hack so we can import from tests/ and from local scripts
try:
    from _compare_outputs import gen_comparator
except ImportError:
    from ._compare_outputs import gen_comparator


def compare(proc, me, verbose=True):
    scores = {'ok': 0, 'nok': 0}
    log = ''

    def myprint(*args):
        nonlocal log
        log += ' '.join(str(x) for x in args) + '\n'

    test = gen_comparator(proc, me, scores, print=myprint)
    # test('beginning')
    # test('short_title')
    # test('long_title')
    # test('end')
    test('url_dossier_assemblee')
    test('url_dossier_senat')
    test('url_jo')
    test('urgence')

    myprint()
    myprint('STEPS:')
    if len(proc['steps']) != len(me['steps']):
        myprint('!! NOK !! DIFFERENT NUMBER OF STEPS:', len(proc['steps']), 'VS', len(me['steps']))
    myprint()

    # hack to re-align if missing a step
    try:
        if proc['steps'][0]['source_url'] == me['steps'][1]['source_url']:
            proc['steps'] = [{}] + proc['steps']
            myprint('   > missing first step in anpy version, added an empty step for fair comparaison')
    except KeyError:
        pass

    for i, step_proc in enumerate(proc['steps']):
        myprint(' - step', i + 1)

        step_me = {}
        if len(me['steps']) > i:
            step_me = me['steps'][i]
        else:
            myprint('  - step not in mine')

        test = gen_comparator(step_proc, step_me, scores, print=myprint)

        # test('date')
        test('institution')
        test('stage')
        test('step')
        test('source_url')
        myprint()

    myprint('NOK:', scores['nok'])
    myprint('OK:', scores['ok'])

    if verbose:
        print(log)
    return log

if __name__ == '__main__':
    proc = json.load(open(sys.argv[1]))
    me = json.load(open(sys.argv[2]))
    compare(proc, me)
