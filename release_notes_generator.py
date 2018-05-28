#
# release_notes_generator.py
# Mich, 2015-06-22
#

import subprocess
import argparse
import re
import os
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--from', required=True, dest='_from',
                        help="Hash before the starting point "
                             "(previous release)")
    parser.add_argument('--to', required=True,
                        help="Hash where to stop (current release)")
    parser.add_argument('--directory', required=True,
                        help="Directory where to run the git commands to "
                             "generate the release notes")
    parser.add_argument('--output-file', default=None,
                        help="File where to output release notes")
    args = parser.parse_args()

    if args.output_file:
        out = open(args.output_file, 'wt')
    else:
        out = sys.stdout

    os.chdir(args.directory)
    _from = args._from
    to = args.to

    p = subprocess.Popen(['git', 'log', '--first-parent',
                          '{}..{}'.format(_from, to)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = p.communicate()
    output = output.decode('utf-8')
    new_block = 0
    multi_line = False
    for line in output.split('\n'):
        if re.findall('^commit [0-9a-f]{40}$', line):
            if multi_line:
                out.write("\n")  # spacing
            multi_line = False
            first_line = True
            new_block = 3
            commit_hash = line[7:]
            out.write(commit_hash[:8] + " - ")
            continue
        if new_block:
            new_block -= 1
            continue
        if line != "":
            if first_line:
                line = line[4:]  # eat starting whitespaces
                first_line = False
            else:
                multi_line = True
                line = " " * 7 + line  # padd hash
            out.write(line + "\n")
    p.wait()
    out.write('\n\n')
    out.flush()

    for cmd in [['git', 'checkout', _from],
                ['git', 'submodule', 'update'],
                ['git', 'checkout', to],
                ['git', 'submodule', 'summary'],
                ['git', 'submodule', 'update']]:
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        p.wait()
        if p.returncode != 0:
            output, _ = p.communicate()
            output = output.decode('utf-8')
            sys.stderr.write(output)
            sys.exit(p.returncode)

    out.close()
