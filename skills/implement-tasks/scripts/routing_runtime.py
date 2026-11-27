"""Runtime eligibility and load when choosing within a matching Routing Rule."""

from dataclasses import dataclass


def pair(entry):
    if (not isinstance(entry, dict) or not isinstance(entry.get('harness'), str)
            or 'model' not in entry or not isinstance(entry['model'], (str, type(None)))):
        raise ValueError('Expected a Harness and model pair in runtime settings.')
    return entry['harness'], entry['model']


@dataclass(frozen=True)
class Usage:
    active: int = 0
    capacity: int | None = None
    quota_remaining: int | None = None
    available: bool = True
    assigned: int = 0

    @classmethod
    def parse(cls, data):
        if not isinstance(data, dict):
            raise ValueError('Expected a runtime capacity object.')
        active = data.get('active', 0)
        capacity = data.get('capacity')
        quota = data.get('quota_remaining')
        available = data.get('available', True)
        assigned = data.get('assigned', 0)
        if any(type(value) is not int or value < 0 for value in (active, assigned)) or type(available) is not bool:
            raise ValueError('Runtime usage requires nonnegative active and assigned counts and boolean availability.')
        if any(value is not None and (type(value) is not int or value < 0) for value in (capacity, quota)):
            raise ValueError('Runtime capacity and remaining quota must be nonnegative integers or null.')
        return cls(active, capacity, quota, available, assigned)

    def has_capacity(self):
        return self.capacity is None or self.active < self.capacity


UNKNOWN = Usage()


class Runtime:
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError('Expected a runtime routing object.')
        harnesses = data.get('harnesses', {})
        models = data.get('models', [])
        allowed_harnesses = data.get('allowed_harnesses')
        allowed_models = data.get('allowed_models')
        if not isinstance(harnesses, dict) or not isinstance(models, list):
            raise ValueError('Expected a Harness usage object and a list of model usage entries.')
        if allowed_harnesses is not None and (not isinstance(allowed_harnesses, list)
                                             or not all(isinstance(item, str) for item in allowed_harnesses)):
            raise ValueError('Expected a list for allowed_harnesses.')
        if allowed_models is not None and not isinstance(allowed_models, list):
            raise ValueError('Expected a list for allowed_models.')
        self.harnesses = {name: Usage.parse(usage) for name, usage in harnesses.items()}
        self.models = {pair(entry): Usage.parse(entry) for entry in models}
        self.allowed_harnesses = None if allowed_harnesses is None else set(allowed_harnesses)
        self.allowed_models = None if allowed_models is None else {pair(entry) for entry in allowed_models}
        self.worker = data.get('worker')
        if self.worker is not None:
            pair(self.worker)
            family = self.worker.get('family')
            if family is not None and not isinstance(family, str):
                raise ValueError('The Worker model family must be text or null.')

    def allows(self, candidate):
        harness, model = pair(candidate)
        return ((self.allowed_harnesses is None or harness in self.allowed_harnesses)
                and (self.allowed_models is None or (harness, model) in self.allowed_models))

    def usage(self, candidate):
        harness, model = pair(candidate)
        return self.harnesses.get(harness, UNKNOWN), self.models.get((harness, model), UNKNOWN)

    def candidates(self, eligible):
        filters = (
            (self.allows, 'the invocation restriction excludes all eligible candidates'),
            (lambda row: all(usage.available for usage in self.usage(row)), 'no eligible Harness or model is available'),
            (lambda row: all(usage.quota_remaining != 0 for usage in self.usage(row)), 'eligible candidates are out of quota'),
            (lambda row: all(usage.has_capacity() for usage in self.usage(row)), 'eligible candidates are at capacity'),
        )
        for keep, reason in filters:
            eligible = [candidate for candidate in eligible if keep(candidate)]
            if not eligible:
                return [], reason
        return eligible, None

    def load(self, candidate):
        return tuple(usage.active for usage in self.usage(candidate))

    def quota(self, candidate):
        # Known remaining quota ranks ahead of unknown quota, larger first.
        known = [usage.quota_remaining for usage in self.usage(candidate) if usage.quota_remaining is not None]
        return (0, -min(known)) if known else (1, 0)

    def assigned(self, candidate):
        return tuple(usage.assigned for usage in self.usage(candidate))
