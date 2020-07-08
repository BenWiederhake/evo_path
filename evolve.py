#!/usr/bin/env python3

import json
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import secrets
import sys
import time


DEFAULT_FILE = 'germany-bw.png'
NUM_LINES = 20

NUM_GENERATIONS = 20
KEEP_SPECIMEN = 20
# TODO: Implement something like MAX_AGE


def make_run_id():
    # For a collision you'd need >>16K invocations in a single millisecond.
    return 'T{}_R{}'.format(str(int(time.time() * 1000)), secrets.token_hex(4))


def make_initial(size, num_lines):
    raise NotImplementedError()


def render_path(path, size):
    raise NotImplementedError()


def compute_penalty(result_img, dst_img):
    raise NotImplementedError()


def run_mutation(population, size):
    raise NotImplementedError()


def run_recombination(population, size):
    raise NotImplementedError()


def run_selection(population, dst_img):
    raise NotImplementedError()


def run_canonicalization(population):
    raise NotImplementedError()


def run_evolution(dst_img, num_lines, generations=NUM_GENERATIONS, render_intermediate_pattern=None):
    # Could make these actual parameters in the future:
    initial_population = None
    inject_initial = False

    if not initial_population:
        population = []
        inject_initial = True
    else:
        population = list(initial_population)

    if inject_initial:
        population.append(make_initial(dst_img.size, num_lines))

    for seqnr in range(generations):
        run_mutation(population, dst_img.size)
        run_recombination(population, dst_img.size)
        run_selection(population, dst_img)
        run_canonicalization(population)

    result_path = population[0]
    result_img = dst_img # render_path(result_path, dst_img.size)
    result_penalty = 10000 # compute_penalty(result_img, dst_img)

    return result_path, result_img, result_penalty


def run_on_file(filename, num_lines):
    run_id = make_run_id()
    print('run_id = {}'.format(run_id))
    dst_img = Image.open(filename).convert('L')
    intermediate = 'output/intermediate_{}_I{{seqnr:08}}.png'.format(run_id)

    result_path, result_img, result_penalty = run_evolution(
        dst_img, num_lines,
        render_intermediate_pattern=intermediate, generations=NUM_GENERATIONS)

    result_basename = 'output/result_{run_id}_P{penalty}.'.format(run_id=run_id, penalty=result_penalty)
    result_img.save(result_basename + 'png')
    with open(result_basename + 'txt', 'w') as fp:
        json.dump(
            {
                'type': 'EVOPATH_RESULT',
                'flavor': 'IRREGULAR_RIDDANCE_VIOLA',
                'input': dict(
                    filename=filename,
                    num_lines=num_lines,
                    ),
                'result_filename': result_basename + 'png',
                'result_path': result_path,
                'result_penalty': result_penalty,
                'size': dst_img.size,
                'render_intermediate_pattern': render_intermediate_pattern,
                'generations': NUM_GENERATIONS,
                'run_id': run_id,
                'parameters': dict(
                    mutation=dict(
                        ),
                    recombination=dict(
                        ),
                    selection=dict(
                        KEEP_SPECIMEN=KEEP_SPECIMEN,
                        ),
                    canonicalization=dict(
                        method='from_middle,rightmost_is_first'
                        ),
                    ),
                },
            fp,
            indent=1,
            sort_keys=True
            )
    print('Success. Written to {0}png and {0}txt'.format(result_basename))


def run():
    usage_line = 'USAGE: {} [GREYSCALE_IMAGE [NUM_LINES]]'.format(sys.argv[0])
    if len(sys.argv) == 1:
        run_on_file(DEFAULT_FILE, NUM_LINES)
    elif len(sys.argv) == 2:
        if sys.argv[1] in '--help -h -help ? -? help'.split():
            print(usage_line)
            print('(If you meant an image-file, try "./{}" or something.)'.format(sys.argv[1]))
            exit(0)
        run_on_file(sys.argv[1], NUM_LINES)
    elif len(sys.argv) == 3:
        run_on_file(sys.argv[1], int(sys.argv[2]))
    else:
        print(usage_line, file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    run()
