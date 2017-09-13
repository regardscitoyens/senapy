import json, sys

proc = json.load(open(sys.argv[1]))
me = json.load(open(sys.argv[2]))

score_ok = 0
score_nok = 0

# i like to write cryptic function sometimes also
def test_test(proc, me):
    def test(a, b=None, a_key=lambda a: a):
        global score_nok, score_ok
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
test('beginning')
test('short_title')
test('long_title', 'long_title_descr')
test('end')
test('url_dossier_assemblee')
test('url_dossier_senat')
test('url_jo')
test('type', 'urgence', lambda type: type == 'urgence')

print()
print('STEPS:')
if len(proc['steps']) != len(me['steps']):
    print('!! NOK !! DIFFERENT NUMBER OF STEPS:', len(proc['steps']), 'VS', len(me['steps']))
print()

for i, step_proc in enumerate(proc['steps']):
    print(' - step', i + 1)

    step_me = {}
    if len(me['steps']) > i:
        step_me = me['steps'][i]
    else:
        print('  - step not in mine')

    test = test_test(step_proc, step_me)

    test('date')
    test('institution')
    test('stage')
    test('step')
    test('source_url')
    print()

print('NOK:', score_nok)
print('OK:', score_ok)