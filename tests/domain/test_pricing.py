from domain.services.pricing import calculate_gst_inclusive, add_money, multiply_money


def test_calculate_gst_inclusive():
    # S$40.00 gross total -> 4000 cents
    # net = 4000 / 1.09 = 3669.72... -> 3670 cents (S$36.70)
    # gst = 4000 - 3670 = 330 cents (S$3.30)
    
    result = calculate_gst_inclusive(4000, 9.0)
    assert result["gross_total_cents"] == 4000
    assert result["net_cents"] == 3670
    assert result["gst_cents"] == 330
    assert result["source_currency"] == "SGD"


def test_calculate_gst_inclusive_zero():
    result = calculate_gst_inclusive(0, 9.0)
    assert result["gross_total_cents"] == 0
    assert result["net_cents"] == 0
    assert result["gst_cents"] == 0


def test_calculate_gst_inclusive_rounding():
    # 1050 cents (S$10.50)
    # net = 1050 / 1.09 = 963.30... -> 963 cents
    # gst = 1050 - 963 = 87 cents
    result = calculate_gst_inclusive(1050, 9.0)
    assert result["net_cents"] == 963
    assert result["gst_cents"] == 87
    assert result["net_cents"] + result["gst_cents"] == 1050


def test_add_money():
    assert add_money(100, 200) == 300


def test_multiply_money():
    assert multiply_money(150, 3) == 450
