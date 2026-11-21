"""
Bot template. Copy this folder to my_bots/<your_team>/ and write decide().

  - decide() is called once per decision and has 2 seconds to return, or your
    bot folds. Crashes and invalid actions also fold; your bot stays in the game.
  - You may use the Python 3.10 standard library, eval7, numpy, scipy, treys
    and scikit-learn. Nothing else is installed in the sandbox.
  - No network, no file writes, no subprocesses, no eval/exec. You may read
    your own data/ folder, at import time only.
  - Check your bot before submitting:  make validate BOT=my_bots/<your_team>

The full list of what decide() receives is in the README ("What your bot
sees"); the most useful keys are summarised below.

RETURN FORMAT:
  {"action": "fold"}
  {"action": "check"}                       # only when can_check is True
  {"action": "call"}
  {"action": "raise", "amount": 1200}       # amount = your TOTAL bet this street
  {"action": "all_in"}

CARDS are strings like "As" (ace of spades) or "Td" (ten of diamonds).
"""

import random  # noqa: F401  (seeded per match, so a seeded match replays exactly)


def decide(game_state: dict) -> dict:
    """
    game_state (the most useful keys):
      your_cards        ["Ah", "Kh"]
      community_cards   [] preflop, then 3, 4, 5 cards
      street            "preflop" | "flop" | "turn" | "river"
      pot, current_bet, min_raise_to, amount_owed, can_check
      your_stack, your_bet_this_street, your_bot_id
      blinds            {"sb", "bb", "ante"} for this hand (they rise every 20 hands)
      hand_num          hand number in this match, from 0
      button_seat, sb_seat, bb_seat, seat_to_act
      players           public info per seat: seat, bot_id, stack, state, bet_this_street, ...
      action_log        every action this hand: {"seat", "bot_id", "action", "amount", "street"}
      match_action_log  the last 200 actions across the match, with "hand_num", plus
                        {"action": "show", "cards": [...]} for each player at a showdown

    Debugging: anything you print() is saved with the decision, and you can add
    a JSON-serialisable "debug" value to what you return, e.g.
    {"action": "call", "debug": {"equity": 0.4}}. Run with: python3 play.py --show
    """
    import time
    try :
        import eval7
    except Exception:
        eval7 = None

    RANKS = "23456789TJQKA"
    gs = game_state

    # --------------------------------helpers----------------------------------- #

    # passive play
    def passive():
        return {"action" : "check"} if gs.get("can_check") else {"action" : "fold"}

    def make_raise(raised_to):
        max_total = gs["your_stack"] + gs["your_bet_this_street"]
        raised_to = int(max(raised_to, gs["min_raise_to"]))

        if raised_to >= max_total * 0.6 or gs["min_raise_to"] >= max_total:
            return {"action" : "all_in"}
        return {"action" : "raise", "amount" : raised_to}

    # based off of Bill Chen's formula for evaluating starting poker hands
    def chen_score(cards):
        rank1, rank2 = sorted((RANKS.index(c[0]) for c in cards), reverse = True)
        score = {12: 10, 11: 8, 10: 7, 9: 6}.get(rank1, (rank1 + 2) / 2) 

        if rank1 == rank2:
            score == max(5, score * 2)
        else:
            if cards[0][1] == cards[1][1]:
                score += 2
            gap = rank1 - rank2 - 1
            score -= [0, 1, 2][gap] if gap < 4 else 5

            if gap <= 1 and rank1 < 10:
                score += 1
        return min(0.85, max(0.30, 0.30 + score * 0.0275))

    # scores detailing opponent habits
    def profile_opponent():
        me = gs.get("your_bot_id")

        actions = [a for a in  gs.get("match_action_log", [])
                   if a.get("bot_id") is not None and a.get("bot_id") != me and 
                   a.get("action") in ("fold", "check", "call", "raise", "all_in")]

        num_acts = len(actions)

        if num_acts < 20: # too small, benchmark is after 1st blind raise
            return 0.25, 0.35, 0.05, num_acts

        folds = sum(a["action"] == "fold" for a in actions)
        aggressive_moves = sum(a["action"] in ("raise", "all_in") for a in actions)
        all_ins = sum(a["action"] == "all_in" for a in actions)
        didnt_fold = max(1, num_acts - folds)

        return folds / num_acts, aggressive_moves / didnt_fold, all_ins / num_acts, num_acts

    fold_rate, aggressive_moves, all_in_rate, samples = profile_opponent()

    # exploitation (dhruv)

    # ---------------------game time game time ---------------------------------#
    if game_state.get("type") == "warmup":     # one call before hand 1; load things here if you like
        return {"action": "check"}

    cards = game_state["your_cards"]
    pot = game_state["pot"]
    owed = game_state["amount_owed"]
    ranks = [c[0] for c in cards]

    """
    if ranks[0] == ranks[1] and ranks[0] in "AKQJ":           # big pocket pair: raise
        raise_to = max(game_state["min_raise_to"], game_state["current_bet"] + pot)
        return {"action": "raise", "amount": raise_to}
    if game_state["can_check"]:
        return {"action": "check"}
    if owed <= pot * 0.25:                                     # cheap to continue: call
        return {"action": "call"}
    return {"action": "fold"}
    """
