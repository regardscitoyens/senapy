import json, sys

def type_to_step(type):
    if not type:
        return
    if 'DEPOT_INITIATIVE' in type:
        return 'depot'
    if 'COMMISSION' in type:
        return 'commission'
    if 'DECISION' in type:
        return 'hemicycle'
    return type


def type_to_stage(type):
    if not type:
        return
    if 'PREMIERE_LECTURE' in type:
        return '1ère lecture'
    if 'DEUXIEME_LECTURE' in type:
        return '2ème lecture'
    if 'TROISIEME_LECTURE' in type:
        return '3ème lecture'
    if 'NOUVELLE_LECTURE' in type:
        return 'nouv. lect.'
    if 'LECTURE_DEFINITIVE' in type:
        return 'l. definitive'
    if 'CMP' in type:
        return 'CMP'
    return type


def type_to_instit(type):
    if not type:
        return
    if 'AN_' in type:
        return 'assemblee'
    if 'SENAT_' in type:
        return 'senat'
    if 'CONSEIL_CONSTITUT' in type:
        return 'conseil constitutionnel'
    if 'CMP' in type:
        return 'CMP'
    return type


def compare(proc, me, verbose=True):
    score_nok, score_ok = 0, 0
    log = ''

    def myprint(*args):
        nonlocal log
        log += ' '.join(str(x) for x in args) + '\n'

    # i like to write cryptic function sometimes also
    def test_test(proc, me):
        def test(a, b=None, a_key=lambda a: a):
            nonlocal myprint, score_ok, score_nok
            if b is None:
                b = a
            a_val = a_key(proc.get(a))
            b_val = me.get(b)
            if a_val != b_val:
                myprint('!! NOK !!', a,' diff:', a_val, 'VS', b_val)
                score_nok += 1
            else:
                myprint('OK', a, '(', a_val, ')')
                score_ok += 1
        return test

    test = test_test(proc, me)
    test('url', 'url_dossier_assemblee')
    # test('title', 'long_title_descr')
    test('senat_url', 'url_dossier_senat')
    test('legislature', 'assemblee_legislature', lambda x: int(x))

    myprint()
    myprint('STEPS:')
    myprint()

    i = 0
    for step_proc in proc['steps']:
        if type(step_proc) is list:
            myprint('INVALID STEP DETECTED (LIST)')
            continue
        for act in step_proc.get('acts', []):

            if 'DEPOT_INITIATIVE' not in act['type'] \
                and 'TEXTE' not in act['type'] \
                and 'DECISION' not in act['type']:
                continue

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

            test('type', 'step', type_to_step)
            test_step('type', 'stage', type_to_stage)
            test_step('type', 'institution', type_to_instit)
            myprint()
            i += 1

    myprint('NOK:', score_nok)
    myprint('OK:', score_ok)

    if verbose:
        print(log)
    return log

if __name__ == '__main__':
    proc = json.load(open(sys.argv[1]))
    me = json.load(open(sys.argv[2]))
    compare(proc, me)

"""
legislature: need senat_url
senat_url not OK in anpy.json
no CC decision / promulgation in anpy.json
"""
