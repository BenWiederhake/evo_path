#!/usr/bin/env python3

import json
from math import ceil, sqrt, pi, sin, cos
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import random
import secrets
import sys
import time


VERBOSE = True
DEFAULT_FILE = 'germany-bw.png'
NUM_LINES = 20

NUM_GENERATIONS = 20
INITIAL_SIZE_PERCENT = 80
MUTATE_POPULATION_PERCENT = 50
MUTATE_GAUSS_SIGMA_PERCENT = 15
RECOMBINE_POPULATION_PERCENT = 30
SELECTION_KEEP_SPECIMEN = 20
# TODO: Implement something like MAX_AGE


def make_run_id():
    # For a collision you'd need >>16K invocations in a single millisecond.
    return 'T{}_R{}'.format(str(int(time.time() * 1000)), secrets.token_hex(4))


def clamp_xy(xy, size):
    return tuple(max(0, min(val, max_val)) for val, max_val in zip(xy, size))


class Specimen:
    def __init__(self, path, size):
        self.path = [clamp_xy(xy, size) for xy in path]
        if VERBOSE:
            print('CREATE path', [(round(x), round(y)) for x, y in self.path])
        self.image = None
        self.penalty = None
        self.size = size

    def mutate(self):
        # TODO: Implement the BetterIdeas™ described in this post:
        # https://www.reddit.com/r/zekach/comments/hmkjx6/how_could_this_be_automated/fx79ton/

        index = random.randrange(len(self.path))

        old_xy = self.path[index]
        new_xy = [random.gauss(val, max_val * MUTATE_GAUSS_SIGMA_PERCENT / 100) for val, max_val in zip(old_xy, self.size)]

        new_path = list(self.path)
        new_path[index] = new_xy

        return Specimen(new_path, self.size)

    def recombine(self, other):
        # TODO: Implement the BetterIdeas™ described in this post:
        # https://www.reddit.com/r/zekach/comments/hmkjx6/how_could_this_be_automated/fx79ton/

        assert self.size == other.size
        assert len(self.path) == len(other.path)

        splice_from = random.randrange(len(self.path))
        splice_until = splice_from
        while splice_until == splice_from:
            splice_until = random.randrange(len(self.path))

        if splice_from > splice_until:
            splice_from, splice_until = splice_until, splice_from
            adam, eve = other.path, self.path
        else:
            adam, eve = self.path, other.path

        new_path = adam[:splice_from] + eve[splice_from:splice_until] + adam[splice_until:]

        return Specimen(new_path, self.size)

    def compute_image(self):
        if self.image is not None:
            return self.image
        raise NotImplementedError()

        return self.image

    def compute_penalty(self, dst_img):
        if self.penalty is not None:
            return self.penalty
        raise NotImplementedError()

        return self.penalty


def make_initial(size, num_lines):
    path = []
    w, h = size
    wc = (w / 2)
    hc = (h / 2)
    wr = (w / 2) * INITIAL_SIZE_PERCENT / 100
    hr = (h / 2) * INITIAL_SIZE_PERCENT / 100
    for i in range(num_lines):
        path.append((
            wc + wr * cos(2 * pi * i / num_lines),
            hc - hr * sin(2 * pi * i / num_lines),
            ))
    return Specimen(path, size)


def sample_percentage(population, percentage):
    n = ceil(len(population) * percentage / 100)
    sample = random.sample(population, n)
    return sample


def run_mutation(population):
    for specimen in sample_percentage(population, MUTATE_POPULATION_PERCENT):
        # Note that the sample *list* is computed before the first `append()` call,
        # so this is perfectly safe and also doesn't double-mutate any specimen.
        population.append(specimen.mutate())

    while len(population) < SELECTION_KEEP_SPECIMEN:
        # The initial population is too low. Fill it up with mutations.
        # Double-mutations are welcome.
        specimen = random.sample(population, 1)[0]
        population.append(specimen.mutate())


def run_recombination(population):
    orig_population = len(population)
    orig_indices = list(range(orig_population))
    for adam_index, eve_index in zip(sample_percentage(orig_indices, RECOMBINE_POPULATION_PERCENT), sample_percentage(orig_indices, RECOMBINE_POPULATION_PERCENT)):
        # We use `sample_percentage` to avoid duplicates.
        # However, this does not cover the case of `adam_index == eve_index`.
        # Since this shouldn't happen too often anyway, we can just respample eve.
        while adam_index == eve_index:
            eve_index = random.randrange(orig_population)

        # Note that the sample *lists* are computed before the first `append()` call,
        # and that rerolling only considers `orig_population`,
        # so this is perfectly safe and also doesn't double-recombine any specimen.
        population.append(population[adam_index].recombine(population[eve_index]))


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
        population = [Specimen(path) for path in initial_population]

    if inject_initial:
        population.append(make_initial(dst_img.size, num_lines))

    for seqnr in range(generations):
        if VERBOSE:
            print()
            print('===== BEGIN GENERATION {} ====='.format(seqnr))
            print('== MUTATE ==')
        run_mutation(population)
        if VERBOSE:
            print('== RECOMBINE ==')
        run_recombination(population)
        if VERBOSE:
            print('== SELECT ==')
        run_selection(population, dst_img)
        if VERBOSE:
            print('== CANONICALIZE ==')
        run_canonicalization(population)

        if render_intermediate_pattern is not None:
            intermediate = population[0]
            intermediate_img = intermediate.compute_img()
            intermediate_img.save(render_intermediate_pattern.format(seqnr=seqnr))

    if VERBOSE:
        print('== END EVOLUTION ==')

    result = population[0]
    # .img and .penalty are already populated due to `run_selection`.
    # However, call`compute_XXX` just in case:
    return result.path, result.compute_img(), result.compute_penalty(dst_img)


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
                    size=dst_img.size,
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
                    initial=dict(
                        SIZE_PERCENT=INITIAL_SIZE_PERCENT,
                        ),
                    mutation=dict(
                        POPULATION_PERCENT=MUTATE_POPULATION_PERCENT,
                        GAUSS_SIGMA_PERCENT=MUTATE_GAUSS_SIGMA_PERCENT,
                        ),
                    recombination=dict(
                        POPULATION_PERCENT=RECOMBINE_POPULATION_PERCENT,
                        ),
                    selection=dict(
                        KEEP_SPECIMEN=SELECTION_KEEP_SPECIMEN,
                        ),
                    canonicalization=dict(
                        method='from_middle,rightmost_is_first',
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
