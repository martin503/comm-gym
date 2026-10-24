import json

import numpy as np

from commgym.offer.instance import OfferCoupon, OfferInstance
from commgym.offer.lexicon import Lexicon


def baseline_completions(
    instance: OfferInstance, level: str, lexicon: Lexicon, rng: np.random.Generator
) -> dict[str, str]:
    """Non-LLM baselines as completion strings: same gate, same judge, zero code forks."""
    shown = instance.slice_for(level)
    by_mass = sorted(
        shown, key=lambda coupon: (-instance.profile.mass(coupon.commodities), coupon.code)
    )
    top = by_mass[0]
    random_pick = shown[int(rng.integers(len(shown)))]
    return {
        'template_top_affinity': _answer(
            [top.code], f'Your usual {_category(top, lexicon)} has an offer this week.'
        ),
        'random_template': _answer(
            [random_pick.code],
            f'Your usual {_category(random_pick, lexicon)} has an offer this week.',
        ),
        # selects sensibly but writes nothing specific: must be gated to 0
        'generic': _answer([top.code], 'Great offers this week, come and see!'),
    }


def _category(coupon: OfferCoupon, lexicon: Lexicon) -> str:
    name = coupon.top_commodities[0]
    return lexicon.displays.get(name, name).lower()


def _answer(selected: list[str], message: str) -> str:
    payload = json.dumps({'selected': selected, 'message': message})
    return f'Baseline.\n<answer>{payload}</answer>'
