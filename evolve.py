#!/usr/bin/env python3

import json
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import secrets
import sys
import time


DEFAULT_FILE = 'germany-bw.png'
NUM_GENERATIONS = 20


def make_run_id():
    # For a collision you'd need >>16K invocations in a single millisecond.
    return 'T{}_R{}'.format(str(int(time.time() * 1000)), secrets.token_hex(4))


def run_evolution(dst_img, initial_population=None, inject_initial=False, generations=NUM_GENERATIONS, render_intermediate_pattern=None):
    #result_path, result_img, result_penalty
    return ['NOT IMPLEMENTED'], dst_img, 10000


def run_on_file(filename):
    run_id = make_run_id()
    print('run_id = {}'.format(run_id))
    dst_img = Image.open(filename).convert('L')
    render_intermediate_pattern = 'intermediate_{}_I{{seqnr:08}}.png'.format(run_id)

    result_path, result_img, result_penalty = run_evolution(dst_img,
        render_intermediate_pattern=render_intermediate_pattern,
        generations=NUM_GENERATIONS)

    result_basename = 'result_{run_id}_P{penalty}.'.format(run_id=run_id, penalty=result_penalty)
    result_img.save(result_basename + 'png')
    with open(result_basename + 'txt', 'w') as fp:
        json.dump(
            {
                'type': 'EVOALG_RESULT',
                'filename': filename,
                'result_filename': result_basename + 'png',
                'result_path': result_path,
                'result_penalty': result_penalty,
                'size': dst_img.size,
                'render_intermediate_pattern': render_intermediate_pattern,
                'generations': NUM_GENERATIONS,
                'run_id': run_id,
            },
            fp,
            indent=1,
            sort_keys=True
        )
    print('Success. Written to {0}png and {0}txt'.format(result_basename))


def run():
    if len(sys.argv) == 1:
        run_on_file(DEFAULT_FILE)
    elif len(sys.argv) == 2:
        run_on_file(sys.argv[1])
    else:
        print('USAGE: {} [GREYSCALE_IMAGE]', file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    run()
