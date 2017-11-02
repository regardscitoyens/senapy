"""
Score how similar are two objects

Returns a function that compares the value of a key between two objects

If two keys are not the same, scores['nok'] and scores['ok']
"""
def gen_comparator(proc, me, scores, print=print):
    def comparator(a, b=None, a_key=lambda a: a, ok_if_correct_is_none=False):
        nonlocal scores, print

        def clean(obj):
            if type(obj) is str:
                # http == https
                obj = obj.replace('http://', 'https://')
                # old senat url
                obj = obj.replace('/dossierleg/', '/dossier-legislatif/')
                # 1ère lecture VS 1ere lecture, should be standardized
                # obj = obj.replace('è', 'e')
                return obj
            return obj

        if b is None:
            b = a
        a_val = clean(a_key(proc.get(a)))
        b_val = clean(me.get(b))
        if a_val != b_val and not (not a_val and not b_val) and not (not a_val and ok_if_correct_is_none):
            # rapport/ta-commission can be guessed
            if not (type(a_val) is str and type(b_val) is str and \
                (a_val.replace('/rapports/', '/ta-commission/') \
                    == b_val.replace('/rapports/', '/ta-commission/')
                )):
                print('!! NOK !!', a,' diff:', a_val, 'VS', b_val)
                scores['nok'] += 1
                return
        print('OK', a, '(', a_val, ')')
        scores['ok'] += 1

    return comparator
