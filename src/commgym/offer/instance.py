from dataclasses import dataclass

MIXED = 'Mixed'
TIERS = ('Private', 'National', 'Mixed')


@dataclass(frozen=True, slots=True)
class OfferCoupon:
    code: str
    campaign: int
    coupon_upc: int
    top_commodities: tuple[str, ...]
    commodities: tuple[str, ...]
    tier: str
    ends_soon: bool
    n_products: int

    @property
    def key(self) -> tuple[int, int]:
        """Coupons are identified by (campaign, coupon_upc): 171 UPCs live in >1 campaign."""
        return (self.campaign, self.coupon_upc)


@dataclass(frozen=True, slots=True)
class ProfileEntry:
    commodity: str
    count: int
    store_share: float


@dataclass(frozen=True, slots=True)
class Profile:
    top: tuple[ProfileEntry, ...]
    overall_store_share: float
    trips_per_week: float
    commodity_counts: dict[str, int]

    def mass(self, commodities: tuple[str, ...]) -> int:
        """Purchase lines the household spent on any of these commodities."""
        return sum(self.commodity_counts.get(commodity, 0) for commodity in commodities)


@dataclass(frozen=True, slots=True)
class OfferInstance:
    instance_id: str
    split: str
    household: int
    day: int
    # pool order: profile-relevant coupons first, distractors after; levels are prefixes,
    # so L1 ⊂ L2 ⊂ L3 with the relevant count constant and distractors growing
    coupons: tuple[OfferCoupon, ...]
    profile: Profile
    level_sizes: dict[str, int]
    n_live_coupons: int
    share_relevant: float

    def slice_for(self, level: str) -> tuple[OfferCoupon, ...]:
        size = self.level_sizes.get(level)
        assert size is not None, f'unknown level {level!r}'
        assert size <= len(self.coupons), f'{level} exceeds the {len(self.coupons)}-coupon pool'
        return self.coupons[:size]

    def codes_for(self, level: str) -> frozenset[str]:
        return frozenset(coupon.code for coupon in self.slice_for(level))
