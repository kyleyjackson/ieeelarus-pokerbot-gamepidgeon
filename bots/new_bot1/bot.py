"""Heads-up practice bot. Opens widely, mixes semi-bluffs with value bets, and bluffs some weak rivers."""

import random

import eval7


# Frequencies by street are ordered flop, turn, river.
BUTTON_OPEN_PLAYABLE = 0.95
BUTTON_OPEN_WEAK = 0.55
LIMP_RAISE_PLAYABLE = 0.55
THREE_BET_BLUFF = 0.38
VALUE_EQUITY = (0.55, 0.59, 0.62)
BET_FRACTION = (0.55, 0.8, 0.95)
BLUFF_CHANCE = (0.62, 0.49, 0.5)
SEMI_BLUFF_RAISE = 0.29
CALL_MARGIN = 0.025

RANKS = "23456789TJQKA"
CARDS = {r + s: eval7.Card(r + s) for r in RANKS for s in "cdhs"}
STREETS = {"flop": 0, "turn": 1, "river": 2}


def preflop_group(cards):
    high, low = sorted((RANKS.index(card[0]) + 2 for card in cards), reverse=True)
    pair = high == low
    suited = cards[0][1] == cards[1][1]
    if (pair and high >= 11) or (high, low) == (14, 13):
        return "premium"
    if (pair and high >= 8) or (high == 14 and low >= 11) or (suited and high >= 12 and low >= 10):
        return "strong"
    if pair or high == 14 or (high >= 11 and low >= 9) or (suited and high - low <= 3):
        return "playable"
    return "weak"


def equity(hole, community, facing_bet):
    """Estimate showdown share. Model a bettor with stronger current hands."""
    known = set(hole + community)
    deck = [card for label, card in CARDS.items() if label not in known]
    hand = [CARDS[label] for label in hole]
    board = [CARDS[label] for label in community]
    pocket_cards = 4 if facing_bet else 2
    points = 0
    trials = 360
    for _ in range(trials):
        draw = random.sample(deck, pocket_cards + 5 - len(board))
        opponent = draw[:2]
        if facing_bet:
            alternative = draw[2:4]
            if eval7.evaluate(alternative + board) > eval7.evaluate(opponent + board):
                opponent = alternative
        complete_board = board + draw[pocket_cards:]
        our_rank = eval7.evaluate(hand + complete_board)
        their_rank = eval7.evaluate(opponent + complete_board)
        if our_rank > their_rank:
            points += 2
        elif our_rank == their_rank:
            points += 1
    return points / (2 * trials)


def raise_to(state, target, effective_total):
    legal_total = max(state["min_raise_to"], min(round(target), effective_total))
    if legal_total >= state["your_stack"] + state["your_bet_this_street"]:
        return {"action": "all_in"}
    return {"action": "raise", "amount": legal_total}


def decide(game_state):
    if game_state.get("type") == "warmup":
        return {"action": "check"}

    s = game_state
    stack = s["your_stack"]
    owed = s["amount_owed"]
    pot = s["pot"]
    current = s["current_bet"]
    invested = s["your_bet_this_street"]
    big_blind = s["blinds"]["bb"]
    opponent = next(p for p in s["players"] if p["seat"] != s["seat_to_act"])
    effective_total = min(invested + stack, opponent["bet_this_street"] + opponent["stack"])
    can_raise = stack > owed and opponent["state"] == "active"
    cost = min(owed, stack)
    pot_after_call = pot - (owed - cost) + cost
    odds = cost / pot_after_call if cost else 0.0

    if s["street"] == "preflop":
        group = preflop_group(s["your_cards"])
        facing_raise = current > big_blind
        on_button = s["button_seat"] == s["seat_to_act"]

        if can_raise and group == "premium":
            target = 3 * max(big_blind, current)
            if effective_total <= 14 * big_blind or current >= 6 * big_blind:
                target = effective_total
            return raise_to(s, target, effective_total)

        if can_raise and not facing_raise:
            if group == "strong":
                return raise_to(s, 3 * big_blind, effective_total)
            open_chance = BUTTON_OPEN_PLAYABLE if on_button else LIMP_RAISE_PLAYABLE
            if group == "weak":
                open_chance = BUTTON_OPEN_WEAK if on_button else 0.0
            if random.random() < open_chance:
                return raise_to(s, 2.5 * big_blind, effective_total)

        if can_raise and facing_raise and current <= 3 * big_blind:
            suited_ace = any(c[0] == "A" for c in s["your_cards"]) and s["your_cards"][0][1] == s["your_cards"][1][1]
            if (group == "strong" or suited_ace) and random.random() < THREE_BET_BLUFF:
                return raise_to(s, 3 * current, effective_total)

        if owed == 0:
            return {"action": "check"}
        if group == "premium":
            return {"action": "call"}
        max_price = {"strong": 0.40, "playable": 0.28, "weak": 0.16}[group]
        if not facing_raise and group == "playable":
            max_price = 0.36
        return {"action": "call"} if odds <= max_price else {"action": "fold"}

    street = STREETS[s["street"]]
    strength = equity(s["your_cards"], s["community_cards"], owed > 0)
    if owed == 0:
        if can_raise:
            value_bet = strength >= VALUE_EQUITY[street]
            bluff_candidate = strength < 0.30 if street == 2 else 0.20 <= strength < 0.52
            if value_bet or (bluff_candidate and random.random() < BLUFF_CHANCE[street]):
                return raise_to(s, invested + pot * BET_FRACTION[street], effective_total)
        return {"action": "check"}

    if can_raise:
        if strength >= (0.83, 0.86, 0.88)[street]:
            return raise_to(s, current + pot + cost, effective_total)
        if street < 2 and 0.30 <= strength <= 0.48 and owed <= pot / 3:
            raised_before = any(a["seat"] == s["seat_to_act"] and a["street"] == s["street"]
                                and a["action"] == "raise" for a in s["action_log"])
            if not raised_before and random.random() < SEMI_BLUFF_RAISE:
                return raise_to(s, current + 0.75 * (pot + cost), effective_total)
    return {"action": "call"} if strength >= odds + CALL_MARGIN else {"action": "fold"}
