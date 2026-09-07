from app.services.adaptive_strategy import choose_experiment_variant

class E:
    id = "x"
    status = "running"
    control = {"hook": "direct"}
    variant = {"hook": "question"}

def test_assignment_is_deterministic():
    e=E()
    assert choose_experiment_variant(e, 0) == "control"
    assert choose_experiment_variant(e, 1) == "variant"
    assert choose_experiment_variant(e, 2) == "control"
