"""Source-dated daily snapshot projection; unknown metrics are never invented."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from .gwt import ProtocolObject, fields
from .models import DailySnapshot, LoseItProtocolError
from .schemas import EPOCH


def _array(value: Any, signature: str) -> list[Any] | None:
    if value is None:
        return None
    if not isinstance(value, ProtocolObject) or value.signature != signature:
        raise LoseItProtocolError("Unexpected Lose It array schema")
    return value.fields


def _number(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float)):
        raise LoseItProtocolError("Unexpected Lose It numeric field")
    number = Decimal(str(value))
    if not number.is_finite():
        raise LoseItProtocolError("Nonfinite Lose It numeric field")
    return number


def parse_daily(details: Any, day: date) -> DailySnapshot:
    """Project only source-supported summary semantics; absent is not zero.

    Nonempty exercise credit remains unknown. Weight uses the returned dated
    RecordedWeight, never GoalsSummary.currentWeight as a historical fallback.
    """
    f = fields(details, "DailyDetails")
    log, exercise_array, food_array = f[3:6]
    foods = _array(
        food_array, "[Lcom.loseit.core.client.model.FoodLogEntry;/3918943916"
    )
    exercises = _array(
        exercise_array, "[Lcom.loseit.core.client.model.ExerciseLogEntry;/1448715428"
    )
    if log is None:
        raise LoseItProtocolError("Lose It diary source date unavailable")
    lf = fields(log, "DailyLogEntry")
    if lf[1] is None:
        raise LoseItProtocolError("Lose It diary source date unavailable")
    calendar = fields(lf[1], "DayDate")
    if type(calendar[1]) is not int:
        raise LoseItProtocolError("Invalid Lose It diary source date")
    if calendar[1] != (day - EPOCH).days:
        raise LoseItProtocolError("Lose It returned a different diary date")
    food_kcal = _number(lf[4])
    budget = None
    if lf[6] is not None:
        budget = _number(fields(lf[6], "DailyLogGoalsState")[0])
    totals: dict[int, Decimal | None] = {13: None, 10: None, 3: None}
    count = None
    if foods is not None:
        totals = {k: Decimal(0) for k in totals}
        count = 0
        for food in foods:
            ff = fields(food, "FoodLogEntry")
            context = fields(ff[1], "FoodLogEntryContext")
            if type(context[5]) is not bool:
                raise LoseItProtocolError("Unknown Lose It food status")
            if context[5]:
                continue
            count += 1
            serving = fields(ff[2], "FoodServing") if ff[2] is not None else None
            nutrients = (
                fields(serving[0], "FoodNutrients")
                if serving and serving[0] is not None
                else None
            )
            if nutrients is None or nutrients[2] is None:
                totals = {k: None for k in totals}
                continue
            base, consumed = _number(nutrients[0]), _number(nutrients[1])
            if base is None or base <= 0 or consumed is None or consumed < 0:
                raise LoseItProtocolError("Invalid Lose It nutrient serving scale")
            if not isinstance(nutrients[2], list):
                raise LoseItProtocolError("Unexpected Lose It nutrient map")
            by_ordinal = {}
            for pair in nutrients[2]:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise LoseItProtocolError("Unexpected Lose It nutrient pair")
                enum, number = pair
                if (
                    not isinstance(enum, ProtocolObject)
                    or enum.signature
                    != (
                        "com.loseit.healthdata.model.shared.food."
                        "FoodMeasurement/2371921172"
                    )
                    or len(enum.fields) != 1
                ):
                    raise LoseItProtocolError("Unexpected Lose It nutrient enum")
                ordinal = enum.fields[0]
                if ordinal in by_ordinal:
                    raise LoseItProtocolError("Duplicate Lose It nutrient key")
                amount = _number(number)
                # First-party hMg preserves -1 as unknown, never scales it.
                by_ordinal[ordinal] = None if amount == -1 else amount
            for ordinal, total in list(totals.items()):
                amount = by_ordinal.get(ordinal)
                totals[ordinal] = (
                    total + amount * consumed / base
                    if total is not None and amount is not None
                    else None
                )
    weight = goal_weight = None
    # bYd multiplies canonical pounds by ApplicationUnits.k for display; hYd
    # sets that multiplier to 1 (lb), .45359237 (kg), or 1/14 (stones).
    pounds_to_kg = Decimal("0.45359237")
    if f[10] is not None:
        wf = fields(f[10], "RecordedWeight")
        weight_calendar = fields(wf[0], "DayDate") if wf[0] is not None else None
        amount = _number(wf[3])
        if weight_calendar is not None and weight_calendar[1] == (day - EPOCH).days:
            if amount is not None and amount > 0:
                weight = amount * pounds_to_kg
    if f[6] is not None:
        goals = fields(f[6], "GoalsSummary")
        # B is the uninitialized flag; n is goalWeight in both pinned layouts.
        if goals[-1] is False:
            amount = _number(goals[10])
            if amount is not None and amount > 0:
                goal_weight = amount * pounds_to_kg
    exercise = Decimal(0) if exercises == [] else None
    net = (
        food_kcal - exercise if food_kcal is not None and exercise is not None else None
    )
    return DailySnapshot(
        day=day,
        budget_kcal=budget,
        food_kcal=food_kcal,
        exercise_kcal=exercise,
        net_kcal=net,
        remaining_kcal=budget - net if budget is not None and net is not None else None,
        protein_g=totals[13],
        carbohydrates_g=totals[10],
        fat_g=totals[3],
        weight_kg=weight,
        goal_weight_kg=goal_weight,
        logged_food_count=count,
    )
