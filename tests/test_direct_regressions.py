def aggregate(findings):
    if "BREACH" in findings: return "BREACH"
    if "INCONCLUSIVE" in findings: return "INCONCLUSIVE"
    if "UNAVAILABLE" in findings: return "UNAVAILABLE"
    return "CLEAN"

def consume(requested, remaining):
    if requested > remaining: raise AssertionError("slash budget exceeded")
    return remaining - requested

def test_unresolved_precedence_is_order_independent():
    assert aggregate(["INCONCLUSIVE", "UNAVAILABLE"]) == "INCONCLUSIVE"
    assert aggregate(["UNAVAILABLE", "INCONCLUSIVE"]) == "INCONCLUSIVE"
    assert aggregate(["UNAVAILABLE", "BREACH"]) == "BREACH"

def test_slash_budget_rejects_overconsumption():
    assert consume(2500, 10000) == 7500
    try: consume(10001, 10000)
    except AssertionError: return
    raise AssertionError("over-budget slash was accepted")
