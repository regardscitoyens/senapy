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
    test('url', 'url_dossier_assemblee')
    test('title', 'long_title_descr')
    test('senat_url', 'url_dossier_senat')
    test('legislature', 'legislature', lambda x: int(x))

    myprint()
    myprint('STEPS:')
    n_steps = 0
    for step in proc['steps']:
        n_steps += len(step['acts'])
    if n_steps != len(me['steps']):
        myprint('!! NOK !! DIFFERENT NUMBER OF STEPS:', n_steps, 'VS', len(me['steps']))
    myprint()

    i = 0
    for step_proc in proc['steps']:
        for act in step_proc['acts']:
            myprint(' - step', i + 1)

            step_me = {}
            if len(me['steps']) > i:
                step_me = me['steps'][i]
            else:
                myprint('  - step not in mine')

            test = test_test(act, step_me)
            test_step = test_test(step_proc, step_me)

            test('date', 'date', lambda date: date.split('T')[0] if date else None)
            test('url', 'source_url')

            def type_to_step(type):
                if 'DEPOT' in type:
                    return 'depot'
                if 'DISCUSSION' in type:
                    return 'commission'
                if 'DECISION' in type:
                    return 'hemicycle'
            test('type', 'step', type_to_step)

            def type_to_stage(type):
                if 'PREMIERE_LECTURE' in type:
                    return '1ère lecture'
                if 'DEUXIEME_LECTURE' in type:
                    return '2ème lecture'
                # TODO
            test_step('type', 'stage', type_to_stage)

            def type_to_instit(type):
                if 'AN_' in type:
                    return 'assemblee'
                if 'SENAT_' in type:
                    return 'senat'
            test_step('type', 'institution', type_to_instit)
            myprint()
            i += 1

    myprint('NOK:', score_nok)
    myprint('OK:', score_ok)
    return score_nok, score_ok

if __name__ == '__main__':
    proc = json.load(open(sys.argv[1]))
    me = json.load(open(sys.argv[2]))
    compare(proc, me)

"""
legislature: need senat_url
senat_url not OK in anpy.json
no CC decision / promulgation in anpy.json
"""
