import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from domain.models.core import Approval, OrderReceipt, QuoteLine, StoreQuote, SubmissionAttempt
from domain.services.fingerprint import (
    build_canonical_payload_v2,
    compute_quote_fingerprint,
    compute_quote_fingerprint_v2,
    explain_fingerprint_diff,
)
from sqlmodel import Session, select

from packages.retailers.base import AuthoritativeCart, CartLine
from packages.retailers.fairprice.adapter import FairPriceAdapter
from tests.conftest import test_engine


# =============================================================================
# PR-07 / Gate 12: Fingerprint V2 & Exact Revalidation Tests
# =============================================================================


def test_fingerprint_v2_canonical_structure_and_hashing():
    lines_a = [
        {'retailer_sku': 'FP_B', 'quantity': 2, 'unit_price_cents': 300, 'line_total_cents': 600},
        {'retailer_sku': 'FP_A', 'quantity': 1, 'unit_price_cents': 500, 'line_total_cents': 500},
    ]
    lines_b = [
        {'retailer_sku': 'FP_A', 'quantity': 1, 'unit_price_cents': 500, 'line_total_cents': 500},
        {'retailer_sku': 'FP_B', 'quantity': 2, 'unit_price_cents': 300, 'line_total_cents': 600},
    ]

    # Deterministic sorting: lines order in input does not change digest
    fp_a, payload_a = compute_quote_fingerprint_v2(
        retailer_id='fairprice',
        lines=lines_a,
        subtotal_cents=1100,
        gross_total_cents=1319,
        delivery_fee_cents=0,
        service_fee_cents=199,
        bag_fee_cents=20,
        delivery_slot_id='slot_fp_morning',
        delivery_slot_window='Tomorrow 08:00 - 10:00 AM',
    )
    fp_b, payload_b = compute_quote_fingerprint_v2(
        retailer_id='fairprice',
        lines=lines_b,
        subtotal_cents=1100,
        gross_total_cents=1319,
        delivery_fee_cents=0,
        service_fee_cents=199,
        bag_fee_cents=20,
        delivery_slot_id='slot_fp_morning',
        delivery_slot_window='Tomorrow 08:00 - 10:00 AM',
    )

    assert fp_a == fp_b
    assert payload_a['schema_version'] == 2
    assert payload_a['currency'] == 'SGD'
    assert payload_a['lines'][0]['sku'] == 'FP_A'
    assert payload_a['lines'][1]['sku'] == 'FP_B'
    assert payload_a['fees']['service_fee_cents'] == 199


def test_fingerprint_v2_tamper_detection_and_explanation():
    lines = [{'retailer_sku': 'FP_A', 'quantity': 1, 'unit_price_cents': 500, 'line_total_cents': 500}]
    fp_orig, payload_orig = compute_quote_fingerprint_v2(
        retailer_id='fairprice',
        lines=lines,
        subtotal_cents=500,
        gross_total_cents=719,
        delivery_slot_id='slot_1',
    )

    # Price modification
    fp_tampered, payload_tampered = compute_quote_fingerprint_v2(
        retailer_id='fairprice',
        lines=lines,
        subtotal_cents=500,
        gross_total_cents=819,
        delivery_slot_id='slot_1',
    )

    assert fp_orig != fp_tampered
    diffs = explain_fingerprint_diff(payload_orig, payload_tampered)
    assert len(diffs) >= 1
    assert any('Gross total changed' in d for d in diffs)


def test_revalidation_fails_on_empty_or_missing_live_cart():
    async def run_test():
        adapter = FairPriceAdapter()

        class ExpectedQuote:
            gross_total_cents = 1453
            lines = [CartLine(retailer_sku='FP_102030', title='Milk', quantity=1, unit_price_cents=635, line_total_cents=635)]

        diff = await adapter.revalidate_cart(ExpectedQuote())
        assert diff.has_changes is True
        assert 'empty or unreadable' in diff.detail.lower()

    asyncio.run(run_test())


def test_revalidation_multiset_line_diff_detection():
    async def run_test():
        adapter = FairPriceAdapter()
        await adapter.add_item_to_cart('FP_102030', 1)
        cart = await adapter.read_cart()

        # 1. Matching quote -> passes
        class MatchingQuote:
            gross_total_cents = cart.gross_total_cents
            lines = [CartLine(retailer_sku='FP_102030', title='Milk', quantity=1, unit_price_cents=635, line_total_cents=635)]

        diff_match = await adapter.revalidate_cart(MatchingQuote())
        assert diff_match.has_changes is False

        # 2. Expected item missing from live cart -> fails
        class MissingItemQuote:
            gross_total_cents = cart.gross_total_cents
            lines = [
                CartLine(retailer_sku='FP_102030', title='Milk', quantity=1, unit_price_cents=635, line_total_cents=635),
                CartLine(retailer_sku='FP_MISSING', title='Bread', quantity=1, unit_price_cents=300, line_total_cents=300),
            ]

        diff_missing = await adapter.revalidate_cart(MissingItemQuote())
        assert diff_missing.has_changes is True
        assert 'FP_MISSING' in diff_missing.items_out_of_stock

        # 3. Live cart has extra unexpected item -> fails
        await adapter.add_item_to_cart('FP_123456', 1)
        diff_extra = await adapter.revalidate_cart(MatchingQuote())
        assert diff_extra.has_changes is True
        assert 'Unexpected items found' in diff_extra.detail

    asyncio.run(run_test())


# =============================================================================
# PR-07 / Gate 13: FairPrice Guarded Idempotent Checkout Tests
# =============================================================================


def test_checkout_fails_closed_when_live_purchase_disabled(monkeypatch):
    monkeypatch.setenv('LIVE_PURCHASE_ENABLED', 'false')

    async def run_test():
        adapter = FairPriceAdapter()
        await adapter.add_item_to_cart('FP_102030', 1)

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.submit_order(approval_token='appr_test123')
        assert 'LIVE_PURCHASE_DISABLED' in str(exc_info.value)

    asyncio.run(run_test())


def test_checkout_fails_closed_when_retailer_not_in_allowlist(monkeypatch):
    monkeypatch.setenv('LIVE_PURCHASE_ENABLED', 'true')
    monkeypatch.setenv('LIVE_PURCHASE_RETAILER_ALLOWLIST', 'shengsiong,littlefarms')

    async def run_test():
        adapter = FairPriceAdapter()
        await adapter.add_item_to_cart('FP_102030', 1)

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.submit_order(approval_token='appr_test123')
        assert 'LIVE_PURCHASE_DISABLED' in str(exc_info.value)

    asyncio.run(run_test())


def test_order_submission_idempotency_on_duplicate_api_request(client, monkeypatch):
    monkeypatch.setenv('LIVE_PURCHASE_ENABLED', 'true')
    monkeypatch.setenv('LIVE_PURCHASE_RETAILER_ALLOWLIST', 'fairprice')

    with Session(test_engine) as session:
        quote = StoreQuote(
            id=uuid4(),
            run_id=uuid4(),
            retailer_id='fairprice',
            cart_fingerprint='fp_mock_val',
            subtotal_cents=635,
            gross_total_cents=1453,
            delivery_fee_cents=599,
            service_fee_cents=199,
            bag_fee_cents=20,
            slot_fee_cents=0,
            derived_net_cents=1333,
            gst_cents=120,
            is_complete=True,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)

        line = QuoteLine(
            id=uuid4(),
            quote_id=quote.id,
            shopping_item_id=uuid4(),
            retailer_sku='FP_102030',
            product_title='Meiji Fresh Milk 2L',
            product_url='https://fairprice.com.sg',
            packs_added=1,
            unit_price_cents=635,
            line_total_cents=635,
            is_in_stock=True,
            is_exact_match=True,
        )
        session.add(line)

        fp = compute_quote_fingerprint(
            retailer_id='fairprice',
            lines=[{'retailer_sku': 'FP_102030', 'quantity': 1, 'unit_price_cents': 635, 'line_total_cents': 635}],
            delivery_slot_id='std_slot',
            subtotal_cents=635,
            delivery_fee_cents=599,
            service_fee_cents=199,
            bag_fee_cents=20,
            gross_total_cents=1453,
        )
        quote.cart_fingerprint = fp
        session.add(quote)

        approval = Approval(
            id=uuid4(),
            quote_id=quote.id,
            approval_token='appr_idem_test',
            idempotency_key='idem_key_123',
            delivery_slot_id='std_slot',
            expected_fingerprint=fp,
            is_used=False,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        session.add(approval)
        session.commit()

        approval_id = str(approval.id)

    from apps.api.core import ADAPTER_MAP
    from packages.retailers.base import SessionStatus
    import asyncio

    test_adapter = FairPriceAdapter()
    asyncio.run(test_adapter.add_item_to_cart('FP_102030', 1))

    async def mock_auth(self):
        return SessionStatus(is_authenticated=True, session_type='authenticated', profile_dir='')

    monkeypatch.setattr(FairPriceAdapter, 'check_session', mock_auth)
    monkeypatch.setitem(ADAPTER_MAP, 'fairprice', lambda: test_adapter)

    resp1 = client.post(f'/approvals/{approval_id}/submit', json={'approval_token': 'appr_idem_test'})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1['status'] == 'CONFIRMED'
    order_id = data1['order_id']
    retailer_order_id = data1['retailer_order_id']

    resp2 = client.post(f'/approvals/{approval_id}/submit', json={'approval_token': 'appr_idem_test'})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2['status'] == 'CONFIRMED'
    assert data2['order_id'] == order_id
    assert data2['retailer_order_id'] == retailer_order_id
