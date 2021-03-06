#!/usr/bin/env python3

import json
from math import atan2, ceil, pi, sin, cos
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import random
import secrets
import sys
import time


VERBOSE = False
DEFAULT_FILE = 'germany-bw.png'
NUM_LINES = 20

NUM_GENERATIONS = 80
INITIAL_SIZE_PERCENT = 80
MUTATE_POPULATION_PERCENT = 60
MUTATE_TELEPORT_PERCENT = 5
MUTATE_GAUSS_SIGMA_PERCENT = 10
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
            print('CREATE path', self.printable_path())
        self.image = None
        self.penalty = None
        self.size = size
        self.is_canonical = False

    def printable_path(self):
        return [(round(x), round(y)) for x, y in self.path]

    def mutate(self):
        # TODO: Implement the BetterIdeas™ described in this post:
        # https://www.reddit.com/r/zekach/comments/hmkjx6/how_could_this_be_automated/fx79ton/

        path = list(self.path)  # Copy

        if random.random() < MUTATE_TELEPORT_PERCENT / 100:
            former_index = random.randrange(len(path))
            new_index = random.randrange(len(path)) - 1
            # `new_index == former_index` means "snap back to the center, and add a random offset
            # Thanks to python's interpretation of negative indices, this "just works".

            path.pop(former_index)
            new_center = tuple((a + b) / 2 for a, b in zip(path[new_index - 1], path[new_index]))
            path.insert(new_index, new_center)

            index = new_index
        else:
            index = random.randrange(len(self.path))

        old_xy = self.path[index]
        new_xy = [random.gauss(val, max_val * MUTATE_GAUSS_SIGMA_PERCENT / 100)
                  for val, max_val in zip(old_xy, self.size)]

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

        self.image = Image.new('L', self.size)
        d = ImageDraw.ImageDraw(self.image)
        # TODO: Try using anti-aliasing and lessen the penalty computation if it's "only" a border pixel
        d.polygon(self.path, fill=(255,))
        del d

        return self.image

    def compute_penalty(self, dst_img):
        if self.penalty is not None:
            return self.penalty

        penalty = 0
        for expected, actual in zip(dst_img.getdata(), self.compute_image().getdata()):
            penalty += abs(actual - expected)

        self.penalty = penalty
        if VERBOSE:
            print('PENALTY {} for path {}'.format(self.penalty, self.printable_path()))
        return self.penalty

    def canonicalize(self):
        if self.is_canonical:
            return

        wc, hc = self.size
        wc /= 2
        hc /= 2

        angles = [atan2(y - hc, x - wc) for x, y in self.path]
        # Poor man's argmin_i(abs(angle[i])):
        _, first_vertex = min((abs(angle), i) for i, angle in enumerate(angles))

        if first_vertex != 0:
            self.path = self.path[first_vertex:] + self.path[:first_vertex]
            # This should not change `image` or `penalty`, so don't invalidate either of these.

        self.is_canonical = True


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
    population.sort(key=lambda specimen: specimen.compute_penalty(dst_img))
    if VERBOSE:
        print('removing {} specimen'.format(len(population) - SELECTION_KEEP_SPECIMEN))
        print('CUTOFF', population[SELECTION_KEEP_SPECIMEN].compute_penalty(dst_img))
    return population[:SELECTION_KEEP_SPECIMEN]


def run_canonicalization(population):
    # TODO: Should also check handedness here.
    # I.e., prevent specimen from going counter-clockwise when the rest is clockwise.
    for specimen in population:
        specimen.canonicalize()


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
        else:
            print('Generation {}'.format(seqnr))
        run_mutation(population)
        if VERBOSE:
            print('== RECOMBINE ==')
        run_recombination(population)
        if VERBOSE:
            print('== SELECT ==')
            print('Judging {} specimen'.format(len(population)))
        population = run_selection(population, dst_img)
        if VERBOSE:
            print('== CANONICALIZE ==')
            print('Now there are {} specimen'.format(len(population)))
        run_canonicalization(population)

        if render_intermediate_pattern is not None:
            intermediate = population[0]
            intermediate_img = intermediate.compute_image()
            intermediate_img.save(render_intermediate_pattern.format(seqnr=seqnr, penalty=intermediate.compute_penalty(dst_img)))

    if VERBOSE:
        print('== END EVOLUTION ==')

    result = population[0]
    # .img and .penalty are already populated due to `run_selection`.
    # However, call`compute_XXX` just in case:
    return result.path, result.compute_image(), result.compute_penalty(dst_img)


def run_on_file(filename, num_lines):
    run_id = make_run_id()
    print('run_id = {}'.format(run_id))
    dst_img = Image.open(filename).convert('L')
    intermediate = 'output/intermediate_{}_I{{seqnr:08}}_P{{penalty:010}}.png'.format(run_id)

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
                'result': dict(
                    filename=result_basename + 'png',
                    path=result_path,
                    penalty=result_penalty,
                    ),
                'render_intermediate_pattern': intermediate,
                'generations': NUM_GENERATIONS,
                'run_id': run_id,
                'parameters': dict(
                    initial=dict(
                        SIZE_PERCENT=INITIAL_SIZE_PERCENT,
                        ),
                    mutation=dict(
                        POPULATION_PERCENT=MUTATE_POPULATION_PERCENT,
                        GAUSS_SIGMA_PERCENT=MUTATE_GAUSS_SIGMA_PERCENT,
                        TELEPORT_PERCENT=MUTATE_TELEPORT_PERCENT,
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
