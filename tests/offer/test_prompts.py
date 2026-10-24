from commgym.offer.instance import OfferCoupon, OfferInstance, Profile
from commgym.offer.lexicon import build_lexicon
from commgym.offer.prompts import system_prompt, user_prompt

LEXICON = build_lexicon(['FLUID MILK PRODUCTS', 'FROZEN PIZZA', 'SOFT DRINKS'])


def _instance() -> OfferInstance:
    def coupon(code: str, commodity: str, ends: bool = False) -> OfferCoupon:
        return OfferCoupon(
            code=code,
            campaign=10,
            coupon_upc=int(code[1:]),
            top_commodities=(commodity,),
            commodities=(commodity,),
            tier='National',
            ends_soon=ends,
            n_products=3,
        )

    return OfferInstance(
        instance_id='offer-dev-7-100',
        split='dev',
        household=7,
        day=100,
        coupons=(
            coupon('k01', 'FLUID MILK PRODUCTS'),
            coupon('k02', 'FROZEN PIZZA'),
            coupon('k03', 'FLUID MILK PRODUCTS', ends=True),
            coupon('k04', 'SOFT DRINKS'),
            coupon('k05', 'FROZEN PIZZA'),
        ),
        profile=Profile(
            top=(),
            overall_store_share=0.31,
            trips_per_week=1.4,
            commodity_counts={'FLUID MILK PRODUCTS': 9, 'FROZEN PIZZA': 3, 'SOFT DRINKS': 1},
        ),
        level_sizes={'L1': 3, 'L2': 5},
        n_live_coupons=40,
        share_relevant=0.5,
    )


def test_system_prompt_states_contract_and_limit():
    system = system_prompt(40)
    assert {'limit': 'at most 40 words' in system, 'contract': '<answer>' in system} == {
        'limit': True,
        'contract': True,
    }


def test_user_prompt_renders_profile_coupons_and_is_stable():
    instance = _instance()
    prompt = user_prompt(instance, 'L2', LEXICON)
    l1 = user_prompt(instance, 'L1', LEXICON)
    assert {
        'display_name': 'Fluid Milk' in prompt,
        'profile': '31%' in prompt,
        'ends_soon': 'ends soon' in prompt,
        'codes': {'k01', 'k03', 'k05'} <= set(prompt.split()),
        'stable': prompt == user_prompt(instance, 'L2', LEXICON),
        'l1_codes_only': {'k04', 'k05'}.isdisjoint(set(l1.split())),
    } == {
        'display_name': True,
        'profile': True,
        'ends_soon': True,
        'codes': True,
        'stable': True,
        'l1_codes_only': True,
    }
