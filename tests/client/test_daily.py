"""Daily semantic coverage using synthetic public-schema objects."""

import asyncio
import json
from datetime import date
from decimal import Decimal

import pytest
from test_client import Response, Session, load
from test_protocol import USER, wire

gwt = load("gwt")
schemas = load("schemas")
snapshot = load("snapshot")

DAY = date(2026, 10, 5)
DETAIL = "com.loseit.core.client.model.DailyDetails/1565598417"
LOG = "com.loseit.core.client.model.DailyLogEntry/612926967"
STATE = "com.loseit.core.client.model.DailyLogGoalsState/1324910267"
DATE = "com.loseit.core.shared.model.DayDate/1611136587"
FOODS = "[Lcom.loseit.core.client.model.FoodLogEntry;/3918943916"
EXERCISES = "[Lcom.loseit.core.client.model.ExerciseLogEntry;/1448715428"


def node(name, fields):
    sig = next(k for k in schemas.LAYOUTS if k.split("/")[0].split(".")[-1] == name)
    return gwt.ProtocolObject(sig, fields)


_DEFAULT_LOG = object()


def details(foods=None, exercises=None, log=_DEFAULT_LOG):
    if log is _DEFAULT_LOG:
        log = gwt.ProtocolObject(
            LOG, [0, gwt.ProtocolObject(DATE, [None, 9409, -6]), 0, 0, None, 0, None, 0]
        )
    return gwt.ProtocolObject(
        DETAIL, [None, None, None, log, exercises, foods, None, 0, None, None, None]
    )


@pytest.mark.parametrize("empty_arrays", [False, True])
def test_all_source_empty_cannot_assert_dated_success(empty_arrays):
    c = load()
    value = details(log=None)
    if empty_arrays:
        value.fields[4:6] = [
            gwt.ProtocolObject(EXERCISES, []),
            gwt.ProtocolObject(FOODS, []),
        ]
    with pytest.raises(c.LoseItProtocolError, match="source date"):
        snapshot.parse_daily(value, DAY)


@pytest.mark.parametrize("calendar", [None, [None, True, -6], [None, "9409", -6]])
def test_undated_metric_payload_is_rejected(calendar):
    c = load()
    log = gwt.ProtocolObject(
        LOG,
        [
            0,
            gwt.ProtocolObject(DATE, calendar) if calendar is not None else None,
            0,
            0,
            Decimal("123"),
            0,
            gwt.ProtocolObject(STATE, [Decimal("456"), None]),
            0,
        ],
    )
    with pytest.raises(c.LoseItProtocolError, match="source date"):
        snapshot.parse_daily(
            details(gwt.ProtocolObject(FOODS, [food({13: "1"})]), log=log), DAY
        )


def test_missing_daily_fields_are_unknown_not_zero():
    c = load()
    result = snapshot.parse_daily(details(), DAY)
    assert result == c.DailySnapshot(DAY)


def test_confirmed_empty_arrays_have_zero_counts_not_missing_values():
    load()
    result = snapshot.parse_daily(
        details(gwt.ProtocolObject(FOODS, []), gwt.ProtocolObject(EXERCISES, [])),
        DAY,
    )
    assert result.logged_food_count == 0
    assert result.food_kcal is None  # No authoritative daily calorie total.
    assert result.exercise_kcal == 0
    assert result.protein_g == 0
    assert result.weight_kg is None


def test_budget_food_remaining_from_explicit_daily_state_with_no_exercises():
    load()
    log = gwt.ProtocolObject(
        LOG,
        [
            0,
            gwt.ProtocolObject(DATE, [0, 9409, -6]),
            0,
            0,
            Decimal("1720.5"),
            0,
            gwt.ProtocolObject(STATE, [Decimal("1600"), None]),
            0,
        ],
    )
    result = snapshot.parse_daily(
        details(gwt.ProtocolObject(FOODS, []), gwt.ProtocolObject(EXERCISES, []), log),
        DAY,
    )
    assert result.budget_kcal == Decimal("1600")
    assert result.food_kcal == Decimal("1720.5")
    assert result.net_kcal == Decimal("1720.5")
    assert result.remaining_kcal == Decimal("-120.5")


def food(nutrients, pending=False):
    measurement = "com.loseit.healthdata.model.shared.food.FoodMeasurement/2371921172"
    pairs = [
        [gwt.ProtocolObject(measurement, [k]), Decimal(v)] for k, v in nutrients.items()
    ]
    nutrition = node("FoodNutrients", [Decimal("2"), Decimal("3"), pairs])
    serving = node("FoodServing", [nutrition, None])
    context = node(
        "FoodLogEntryContext",
        [None, None, False, 0, 0, pending, None, None, None, None],
    )
    return node("FoodLogEntry", [None, context, serving, False, 0, 0, None])


def test_macros_scaled_pending_excluded_missing_nutrient_propagates():
    load()
    foods = gwt.ProtocolObject(
        FOODS,
        [
            food({13: "10", 10: "20", 3: "0"}),
            food({13: "2", 3: "4"}),
            food({13: "999", 10: "999", 3: "999"}, True),
        ],
    )
    result = snapshot.parse_daily(details(foods), DAY)
    assert result.logged_food_count == 2
    assert result.protein_g == Decimal("18")
    assert result.fat_g == Decimal("6")
    assert result.carbohydrates_g is None
    assert result.food_kcal is None


def test_source_minus_one_nutrient_sentinel_is_unknown_not_negative_grams():
    load()
    foods = gwt.ProtocolObject(FOODS, [food({13: "-1", 10: "20", 3: "0"})])
    result = snapshot.parse_daily(details(foods), DAY)
    assert result.protein_g is None
    assert result.carbohydrates_g == Decimal("30")
    assert result.fat_g == 0


def test_nonempty_exercise_never_uses_name_heuristic_or_blind_sum():
    load()
    result = snapshot.parse_daily(
        details(
            exercises=gwt.ProtocolObject(
                EXERCISES, [node("ExerciseLogEntry", [None] * 12)]
            ),
        ),
        DAY,
    )
    assert result.exercise_kcal is None
    assert result.net_kcal is None


def test_daily_recorded_weight_and_goal_are_canonical_pounds_not_display_units():
    load()
    value = details()
    value.fields[10] = node(
        "RecordedWeight",
        [gwt.ProtocolObject(DATE, [0, 9409, -6]), False, 0, Decimal("200")],
    )
    goal_fields = [
        None,
        None,
        False,
        Decimal(0),
        None,
        None,
        Decimal("999"),
        None,
        None,
        None,
        Decimal("150"),
        False,
        Decimal("70"),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Decimal("220"),
        False,
    ]
    value.fields[6] = gwt.ProtocolObject(
        "com.loseit.core.client.model.GoalsSummary/26794011", goal_fields
    )
    result = snapshot.parse_daily(value, DAY)
    assert result.weight_kg == Decimal("90.71847400")
    assert result.goal_weight_kg == Decimal("68.03885550")


def test_recorded_weight_from_another_day_is_not_substituted():
    load()
    value = details()
    value.fields[10] = node(
        "RecordedWeight",
        [gwt.ProtocolObject(DATE, [0, 9408, -6]), False, 0, Decimal("200")],
    )
    assert snapshot.parse_daily(value, DAY).weight_kg is None


def test_wrong_calendar_day_fails():
    c = load()
    log = gwt.ProtocolObject(
        LOG,
        [0, gwt.ProtocolObject(DATE, [0, 9408, -6]), 0, 0, Decimal("0"), 0, None, 0],
    )
    with pytest.raises(c.LoseItProtocolError):
        snapshot.parse_daily(details(log=log), DAY)


def dated_empty_wire():
    return wire(
        [
            1,
            0,
            0,
            "A",
            2,
            0,
            0,
            0,
            5,
            0,
            6,
            0,
            9409,
            -6,
            0,
            0,
            0,
            0,
            0,
            "A",
            3,
            0,
            4,
            0,
            0,
            "A",
            0,
            0,
            0,
            0,
        ],
        [
            "com.loseit.core.client.service.responses.LoseItRemoteServiceResponse/1071940969",
            DETAIL,
            EXERCISES,
            FOODS,
            LOG,
            DATE,
        ],
    )


def test_async_day_sends_only_allowlisted_read_and_decodes_real_wire():
    c = load()
    identity = wire([1, 731, 2, -6], [USER, "synthetic-user"])
    html = "window.embedded_4ppl1c4710n = " + json.dumps(identity[4:])
    # Explicit source-dated empty diary in publicly observed serializer order.
    rpc = dated_empty_wire()
    session = Session(Response(body=html), Response(body=rpc))
    client = c.LoseItClient(session, {"liauth": "synthetic"})
    result = asyncio.run(client.async_get_day(DAY))
    assert result.logged_food_count == 0
    assert result.day == DAY
    method, url, kwargs = session.calls[-1]
    assert method == "POST"
    assert url == "https://www.loseit.com/web/service"
    assert "getDailyDetailsIncludingPendingForDate" in kwargs["data"]
    assert "|9409|-6|" in kwargs["data"]
    assert kwargs["headers"]["Content-Type"].startswith("text/x-gwt-rpc")
    assert kwargs["cookies"] == {"liauth": "synthetic"}


def test_day_rejects_datetime_and_unknown_methods():
    c = load()
    from datetime import datetime

    with pytest.raises(ValueError):
        asyncio.run(
            c.LoseItClient(Session(), {"x": "y"}).async_get_day(datetime(2026, 1, 1))
        )
