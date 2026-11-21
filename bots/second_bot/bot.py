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

CARDS are stringame_state like "As" (ace of spades) or "Td" (ten of diamonds).
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

    # preflop - am i gonna use this?
    PREFLOP_EQ = {
            "AA": 0.852, "AKs": 0.671, "AKo": 0.653, "AQs": 0.662, "AQo": 0.644, "AJs": 0.654, "AJo": 0.636, "ATs": 0.646,
            "ATo": 0.628, "A9s": 0.628, "A9o": 0.607, "A8s": 0.618, "A8o": 0.598, "A7s": 0.610, "A7o": 0.589, "A6s": 0.599,
            "A6o": 0.576, "A5s": 0.599, "A5o": 0.578, "A4s": 0.590, "A4o": 0.567, "A3s": 0.582, "A3o": 0.558, "A2s": 0.573,
            "A2o": 0.549, "KK": 0.824, "KQs": 0.634, "KQo": 0.614, "KJs": 0.626, "KJo": 0.606, "KTs": 0.618, "KTo": 0.597,
            "K9s": 0.600, "K9o": 0.579, "K8s": 0.583, "K8o": 0.560, "K7s": 0.575, "K7o": 0.551, "K6s": 0.566, "K6o": 0.542,
            "K5s": 0.558, "K5o": 0.532, "K4s": 0.549, "K4o": 0.524, "K3s": 0.540, "K3o": 0.515, "K2s": 0.532, "K2o": 0.505,
            "QQ": 0.799, "QJs": 0.602, "QJo": 0.582, "QTs": 0.595, "QTo": 0.572, "Q9s": 0.576, "Q9o": 0.553, "Q8s": 0.561,
            "Q8o": 0.536, "Q7s": 0.543, "Q7o": 0.517, "Q6s": 0.536, "Q6o": 0.510, "Q5s": 0.528, "Q5o": 0.501, "Q4s": 0.519,
            "Q4o": 0.491, "Q3s": 0.510, "Q3o": 0.483, "Q2s": 0.502, "Q2o": 0.474, "JJ": 0.775, "JTs": 0.576, "JTo": 0.552,
            "J9s": 0.557, "J9o": 0.532, "J8s": 0.540, "J8o": 0.516, "J7s": 0.523, "J7o": 0.497, "J6s": 0.506, "J6o": 0.478,
            "J5s": 0.499, "J5o": 0.473, "J4s": 0.491, "J4o": 0.462, "J3s": 0.482, "J3o": 0.452, "J2s": 0.474, "J2o": 0.444,
            "TT": 0.750, "T9s": 0.541, "T9o": 0.515, "T8s": 0.523, "T8o": 0.497, "T7s": 0.506, "T7o": 0.479, "T6s": 0.489,
            "T6o": 0.461, "T5s": 0.472, "T5o": 0.442, "T4s": 0.465, "T4o": 0.434, "T3s": 0.457, "T3o": 0.426, "T2s": 0.448,
            "T2o": 0.417, "99": 0.721, "98s": 0.508, "98o": 0.480, "97s": 0.492, "97o": 0.463, "96s": 0.475, "96o": 0.445,
            "95s": 0.457, "95o": 0.426, "94s": 0.439, "94o": 0.406, "93s": 0.433, "93o": 0.400, "92s": 0.424, "92o": 0.391,
            "88": 0.692, "87s": 0.479, "87o": 0.450, "86s": 0.463, "86o": 0.433, "85s": 0.446, "85o": 0.414, "84s": 0.427,
            "84o": 0.394, "83s": 0.409, "83o": 0.375, "82s": 0.403, "82o": 0.369, "77": 0.662, "76s": 0.453, "76o": 0.423,
            "75s": 0.437, "75o": 0.405, "74s": 0.418, "74o": 0.386, "73s": 0.400, "73o": 0.366, "72s": 0.381, "72o": 0.346,
            "66": 0.632, "65s": 0.432, "65o": 0.401, "64s": 0.414, "64o": 0.380, "63s": 0.395, "63o": 0.362, "62s": 0.376,
            "62o": 0.341, "55": 0.602, "54s": 0.414, "54o": 0.382, "53s": 0.397, "53o": 0.362, "52s": 0.378, "52o": 0.343,
            "44": 0.570, "43s": 0.387, "43o": 0.350, "42s": 0.369, "42o": 0.332, "33": 0.537, "32s": 0.361, "32o": 0.323,
            "22": 0.503,
        }

    # --------------------------------helpers----------------------------------- #

    #! determine equity pre-flop (might b needed for time constraints - claude generated)
    def preflop_equity(cards):
        """Instant table lookup, e.g. ['Ah','Kh'] -> 'AKs' -> 0.671."""
        order = "AKQJT98765432"
        a, b = sorted(cards, key=lambda c: order.index(c[0]))
        if a[0] == b[0]:
            key = a[0] + b[0]
        else:
            key = a[0] + b[0] + ("s" if a[1] == b[1] else "o")
        return PREFLOP_EQ[key]

    # passive play
    def passive():
        return {"action" : "check"} if game_state.get("can_check") else {"action" : "fold"}

    def make_raise(raised_to):
        max_total = game_state["your_stack"] + game_state["your_bet_this_street"]
        raised_to = int(max(raised_to, game_state["min_raise_to"]))

        if raised_to >= max_total * 0.6 or game_state["min_raise_to"] >= max_total:
            return {"action" : "all_in"}
        return {"action" : "raise", "amount" : raised_to}

    # scores detailing opponent habits
    def profile_opponent():
        me = game_state.get("your_bot_id")

        actions = [a for a in  game_state.get("match_action_log", [])
                   if a.get("bot_id") is not None and a.get("bot_id") != me and 
                   a.get("action") in ("fold", "check", "call", "raise", "all_in")]

        num_acts = len(actions)

        if num_acts < 20: # too small, benchmark is after 1st blind raise
            return 0.25, 0.35, 0.05, num_acts, 0.25

        folds = sum(a["action"] == "fold" for a in actions)
        aggressive_moves = sum(a["action"] in ("raise", "all_in") for a in actions)
        all_ins = sum(a["action"] == "all_in" for a in actions)
        didnt_fold = max(1, num_acts - folds)
        fold_to_bet = folds / max(1, folds + sum(a["action"] == "call" for a in actions) + aggressive_moves)

        return folds / num_acts, aggressive_moves / didnt_fold, all_ins / num_acts, num_acts, fold_to_bet

    # determining equity by comparison against many random draws
    def determine_equity(hand, board, max_time = 0.6, max_iterations = 5000):
        known = set(hand + board)
        deck = [eval7.Card(r + s) for r in RANKS for s in "hdsc" if r + s not in known]

        hand0 = [eval7.Card(c) for c in hand]
        board0 = [eval7.Card(c) for c in board]
        remaining_board = 5 - len(board0)
        wins, iterations = 0.0, 0
        deadline = time.time() + max_time

        while iterations < max_iterations and (iterations % 200 or time.time() < deadline):
            random_draw = random.sample(deck, remaining_board + 2)
            full_board = board0 + random_draw[:remaining_board]
            my_cards = eval7.evaluate(hand0 + full_board)
            opp_cards = eval7.evaluate(random_draw[remaining_board:] + full_board)

            if my_cards > opp_cards:
              wins += 1
            elif my_cards == opp_cards:
              wins += 0.5
            iterations += 1

        return wins / max(1, iterations)

    # bluff break-even, MDF, equity to call
    def betting_threshold(bet, pot):
        pot, bet = max(1, pot), max(1, bet)
        return bet / (pot + bet), pot / (pot + bet), bet / (pot + (bet * 2))

    # -------------------------------------- end of helpers ---------------------------------- #

    # ---------------------game time game time (decision making) ---------------------------------#
    if game_state.get("type") == "warmup":     # one call before hand 1; load thingame_state here if you like
        return {"action": "check"}

    try:

        # exploitation
        fold_rate, aggression_rate, all_in_rate, samples, fold_to_bet = profile_opponent()
        bluff_multiplier = 1.0
        call_width_modifier = 0
        val_bet_modifier = 0

        if fold_to_bet > 0.75: # opp folds a lot = bluff more!
            bluff_multiplier = 1.5

        elif fold_to_bet < 0.25: # calling station = mayb dont bluff, thin bets
            bluff_multiplier = 0.5
            val_bet_modifier = -0.05

        if aggression_rate > 0.5: # genuine psychopath = dont take chances
            call_width_modifier = -0.05

        elif aggression_rate < 0.25: # passive player = likely have strong hands whdn they go in
            call_width_modifier = 0.05

        # end of exploitation
        
        cards = game_state["your_cards"]
        pot = game_state["pot"]
        owed = game_state["amount_owed"]
        street = game_state["street"]
        my_stack = game_state["your_stack"]
        big_blind = game_state["blinds"]["bb"]
        ante = game_state["blinds"]["ante"]
        pot_odds = owed / (pot + owed)
        is_button = game_state.get("button_seat") == game_state["seat_to_act"]
        debug = {"opp": [round(fold_rate, 2), round(aggression_rate, 2), samples]}

        # preflop decision making
        if street == "preflop":
            equity = preflop_equity(cards)

            # strong hand: raise to 3x the biggest bet so far
            if equity >= 0.65 and my_stack > owed:
                return make_raise(3 * max(big_blind, game_state["current_bet"]))

            # free look at the flop as big blind
            if game_state["can_check"]:
                return {"action": "check"}

            # otherwise same logic as postflop: call if the price is right
            call_cost = min(owed, my_stack)
            needed = call_cost / (pot + call_cost)
            extra = 0.05 if owed > big_blind else 0      # tighter when facing a real raise
            if equity >= needed + call_width_modifier + extra:
                return {"action": "call"}
            return {"action": "fold"}

        # Postflop decision making
        else:
            equity = determine_equity(cards, game_state["community_cards"])

            # Minimum equity to bet, minimum equity to raise, opening bet size
            bet_at, raise_at, bet_fraction = {
                "flop":  (0.60, 0.80, 1 / 3),
                "turn":  (0.65, 0.85, 2 / 3),
                "river": (0.70, 0.90, 3 / 4),
            }[street]

            can_raise = game_state["your_stack"] > owed and any(
                p["seat"] != game_state["seat_to_act"] and p["state"] == "active"
                for p in game_state["players"]
            )

            # Nobody has bet. Value-bet a strong hand or check.
            if game_state["can_check"]:
                if can_raise and equity >= bet_at + val_bet_modifier:
                    bet_to = game_state["your_bet_this_street"] + round(pot * bet_fraction)
                    return make_raise(bet_to)

                if can_raise and street == "river" and equity < 0.35:
                    bet = round(pot * bet_fraction)
                    bluff_chance = bet / (pot + 2 * bet) * bluff_multiplier
                    if random.random() < bluff_chance:
                        return make_raise(game_state["your_bet_this_street"] + bet)
                return {"action": "check"}

            # Facing a bet. Raise strong hands when the opponent can respond.
            if can_raise and equity >= raise_at:
                return make_raise(3 * game_state["current_bet"])

            # Call or fold using only the chips you can actually match.
            call_cost = min(owed, game_state["your_stack"])
            matched_pot = pot - (owed - call_cost)
            pot_odds = call_cost / (matched_pot + call_cost)

            if equity >= pot_odds + call_width_modifier:
                return {"action": "call"}
            return {"action": "fold"}

            


    except Exception:
        import traceback
        print(traceback.format_exc())
        return passive()
