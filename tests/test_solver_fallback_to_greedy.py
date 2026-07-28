from proxlb.utils.config_parser import Config


def test_solver_fallback_to_greedy_defaults_true():
    cfg = Config.Solver()
    assert cfg.fallback_to_greedy is True


def test_solver_fallback_to_greedy_can_be_disabled():
    cfg = Config.Solver(fallback_to_greedy=False)
    assert cfg.fallback_to_greedy is False
