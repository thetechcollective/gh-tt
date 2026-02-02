from hypothesis import settings

# Hypothesis profiles
# To run e.g. the "a_lot" profile --> `pytest -m hypothesis --hypothesis-profile a_lot`

settings.register_profile('1000', max_examples=1000)
settings.register_profile('10000', max_examples=10000)
settings.register_profile('100000', max_examples=100000)
