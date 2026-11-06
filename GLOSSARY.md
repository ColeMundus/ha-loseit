# Lose It! integration

Language for connecting a Lose It! account to Home Assistant and interpreting its
food diary, calorie allowance and weight information.

## Language

### Account and access

**Lose It! account**:
The service identity to which a person's diary, goals and weight information belong.
Changing the way access is established does not change the account.
_Avoid_: Login, session

**Initial sign-in**:
Establishing access to a Lose It! account using the person's sign-in credentials
and any required human verification.
_Avoid_: Session renewal, refresh

**Lose It! session**:
An established authorization to access a Lose It! account. Website and mobile-app
sessions are distinct access contexts; one does not imply access through the other.
_Avoid_: Account, password

**Session renewal**:
Continuing access using an existing session's renewal credentials, rather than
performing another initial sign-in.
_Avoid_: Password login, automatic sign-in

### Diary and calories

**Diary day**:
The calendar date to which food entries, exercise entries and daily totals belong,
as distinct from the time those values are retrieved.
_Avoid_: Refresh date, fetch date

**Consumed food entry**:
A food entry recorded as eaten, rather than planned for later consumption.
_Avoid_: Planned food, pending food

**Pending food entry**:
A food entry planned but not recorded as eaten.
_Avoid_: Consumed food entry

**Daily calorie budget**:
The calorie allowance reported for a diary day.
_Avoid_: Remaining calories, food calories

**Food calories**:
The energy recorded as consumed for a diary day.
_Avoid_: Daily calorie budget, net calories

**Exercise credit**:
The exercise-related calorie allowance recognized toward a diary day's balance,
which is not necessarily the sum of reported calories burned.
_Avoid_: Raw calories burned, tracker calories

**Net calories**:
Food calories less exercise credit for the same diary day.
_Avoid_: Food calories, remaining calories

**Remaining calories**:
The daily calorie budget less net calories for the same diary day.
_Avoid_: Daily calorie budget, net calories

### Weight

**Diary-day weight**:
A weight value associated with a diary day; its presence alone does not establish
that a new measurement was taken that day.
_Avoid_: New weigh-in, latest measurement

**Weigh-in**:
An explicitly recorded weight measurement associated with a measurement date.
_Avoid_: Diary-day weight

**Goal weight**:
The target body weight reported by Lose It!, distinct from measured weight.
_Avoid_: Current weight, historical goal weight
