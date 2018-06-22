import sys
import os
import requests

if len(sys.argv) != 3:
    print('usage: python add_regression_case.py <dosleg_url> <new_regression_directory>')
    sys.exit()

url = sys.argv[1]
output_directory = sys.argv[2]

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

with open(os.path.join(output_directory, 'input.html'), 'w') as f:
    f.write(requests.get(url).text + '<!-- URL_SENAT=%s -->' % url)

with open(os.path.join(output_directory, 'anpy.json'), 'w') as f:
    f.write('')

print('now you can run regen_regressions_output.py to generate the output of reference')
