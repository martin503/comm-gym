import numpy as np

from commgym.offer.baselines import baseline_completions
from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.instance import OfferCoupon, OfferInstance, Profile
from commgym.offer.lexicon import build_lexicon
from commgym.offer.reward import grade

LEXICON = build_lexicon(['FLUID MILK PRODUCTS', 'FROZEN PIZZA', 'SOFT DRINKS'])
COMMODITIES = ['FLUID MILK PRODUCTS', 'FROZEN PIZZA', 'SOFT DRINKS']


def _instance() -> OfferInstance:
    def coupon(code: str, commodity: str) -> OfferCoupon:
        return OfferCoupon(
            code=code,
            campaign=10,
            coupon_upc=int(code[1:]),
            top_commodities=(commodity,),
            commodities=(commodity,),
            tier='National',
            ends_soon=False,
            n_products=3,
        )

    return OfferInstance(
        instance_id='offer-dev-1-20',
        split='dev',
        household=1,
        day=20,
        coupons=(
            coupon('k01', 'FLUID MILK PRODUCTS'),
            coupon('k02', 'FROZEN PIZZA'),
            coupon('k03', 'SOFT DRINKS'),
        ),
        profile=Profile(
            top=(),
            overall_store_share=0.2,
            trips_per_week=1.0,
            commodity_counts={'FLUID MILK PRODUCTS': 10, 'FROZEN PIZZA': 2},
        ),
        level_sizes={'L1': 3},
        n_live_coupons=3,
        share_relevant=2 / 3,
    )


def _grade_all() -> dict[str, float]:
    instance = _instance()
    completions = baseline_completions(instance, 'L1', LEXICON, np.random.default_rng(0))
    return {
        name: grade(text, instance, 'L1', LEXICON, GateConfig(), RewardConfig()).reward
        for name, text in completions.items()
    }


def test_template_passes_generic_fails():
    rewards = _grade_all()
    assert {
        'template_positive': rewards['template_top_affinity'] > 0,
        'generic_zero': rewards['generic'] == 0.0,
        'template_beats_random': rewards['template_top_affinity'] > rewards['random_template'],
    } == {'template_positive': True, 'generic_zero': True, 'template_beats_random': True}
