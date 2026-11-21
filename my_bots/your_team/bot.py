# TEAM GAMEPIGEON'S BOT FOR IEEE LARUS POKERBOT CONTEST 
# 一夫当关，万付某开！
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

    #* preflop equities table - claude generated
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

    #* determine equity pre-flop (might b needed for time constraints - claude generated)
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

        if num_acts < 20: # too small, benchmark is after 1st blind increase
            return 0.25, 0.35, 0.05, num_acts, 0.5

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
            opp_hole = random_draw[remaining_board:]
            opp_cards = eval7.evaluate(opp_hole + full_board)

            if my_cards > opp_cards:
              wins += 1
            elif my_cards == opp_cards:
              wins += 0.5

            iterations += 1

        return wins / max(1, iterations)

    # -------------------------------------- end of helpers ---------------------------------- #

    # ---------------------game time game time (decision making) ---------------------------------#
    if game_state.get("type") == "warmup":     # one call before hand 1; load things here if you like
        return {"action": "check"}

    try:

        # exploitation
        #! fold_rate, all_in_rate, samples due to needing to reduce the scope of our bot's calculations
        fold_rate, aggression_rate, all_in_rate, samples, fold_to_bet = profile_opponent()  
        call_width_modifier = 0

        if aggression_rate > 0.5: # genuine psychopath 
            call_width_modifier = -0.05

        elif aggression_rate < 0.25: # passive player
            call_width_modifier = 0.05

        # end of exploitation
        
        cards = game_state["your_cards"]
        pot = game_state["pot"]
        owed = game_state["amount_owed"]
        street = game_state["street"]
        #!my_stack = game_state["your_stack"]
        big_blind = game_state["blinds"]["bb"]
        #!ante = game_state["blinds"]["ante"]
        pot_odds = owed / (pot + owed)
        is_button = game_state.get("button_seat") == game_state["seat_to_act"]

        # preflop decision making
        if street == "preflop":
            equity = preflop_equity(cards)

            effective_chips = min(
                [game_state["your_stack"] + game_state["your_bet_this_street"]]
                + [p.get("stack", 0) + p.get("bet_this_street", 0)
                   for p in game_state.get("players", []) if p.get("seat") != game_state["seat_to_act"]
                   and p.get("state") != "folded"]
            ) # smallest chip pile is the effective one, make sure they havent folded

            bb_eff_chips = effective_chips / big_blind
            ranks = sorted((c[0] for c in cards), key = RANKS.index, reverse = True)

            # reading moves
            log = [a for a in game_state.get("action_log", []) if a.get("street") == "preflop"]
            num_raises = sum(1 for a in log if a.get("action") in ("raise", "all_in"))
            facing_all_in = any(a.get("action") == "all_in" for a in log)

            if facing_all_in:
                act = {"action" : "call"} if equity >= pot_odds + call_width_modifier else passive()

            elif bb_eff_chips <= 20 and bb_eff_chips >= 10:
                all_in_thresh = bb_eff_chips * 0.007 + 0.30 if (num_raises == 0) else 0.50
                act = {"action" : "all_in"} if equity >= all_in_thresh else passive()

            else:
                if num_raises == 0:
                    raise_at = 0.45 if is_button else 0.60

                else:
                    raise_at = {1: 0.60, 2: 0.70}.get(num_raises, 0.75)

                call_at = pot_odds + 0.05 * num_raises + call_width_modifier
                suited = cards[0][1] == cards[1][1]
                bluff = suited and "A" in ranks and bool(set(ranks) & set("2345")) and num_raises <= 1 and random.random() < 0.3

                if equity >= raise_at or bluff:
                    act = make_raise(big_blind * 2.5)
                elif num_raises > 0 and equity >= call_at:
                    act = {"action" : "call"}
                elif num_raises == 0 and is_button and owed < big_blind and equity >= 0.36: # dont fold cheap small-blinds (claude suggestion)
                    act = {"action" : "call"}
                else:
                    act = passive()
                
        # postflop decision making
        else:
            board = game_state["community_cards"]
            #!seat = game_state["seat_to_act"]
            bet = game_state["your_bet_this_street"]
            current_bet = game_state["current_bet"]
            equity = determine_equity(cards, board)

            # betting guidelines based on board state
            bet_fraction = {"flop" : 1/3, "turn" : 2/3, "river" : 2/3}
            bet_cases = {"flop" : 0.60, "turn" : 0.65, "river" : 0.69}
            raise_cases = {"flop" : 0.80, "turn" : 0.85, "river" : 0.87}

            # who's been aggro this street
            street_log = [a for a in game_state.get("action_log", []) if a.get("street") == street]
            aggressive_moves = ("raise", "all_in")

            if game_state.get("can_check"):
                if equity >= bet_cases[street]:
                    act = make_raise(bet + bet_fraction[street] * pot)
                else:
                    act = passive()

            else: # opp bet
                me = game_state.get("your_bot_id")
                opp_aggro = [a for a in street_log if a.get("bot_id") != me and a.get("action") in aggressive_moves]
                opp_raises = len(opp_aggro)
                facing_all_in = any(a.get("action") == "all_in" for a in opp_aggro)
                pot_after_call = pot + owed

                # ask for more equity the more the opp has raised this st
                call_at = pot_odds + call_width_modifier + 0.04 * opp_raises

                # big overbets, tighten up
                if owed > pot - owed:
                    call_at += 0.03

                # cheap price on the river, don't get bluffed off a decent hand
                if street == "river" and pot_odds < 0.2:
                    call_at -= 0.03

                raise_at = raise_cases[street] + 0.05 * max(0, opp_raises - 1)

                # semi-bluff raise
                semi_bluff = (street != "river" and not facing_all_in and opp_raises == 1 and 0.35 <= equity <= 0.55 
                              and fold_to_bet > 0.5 and random.random() < 0.2)

                if facing_all_in:
                    act = {"action": "call"} if equity >= call_at else {"action": "fold"}

                elif equity >= raise_at or semi_bluff:
                    raise_to = current_bet + bet_fraction[street] * pot_after_call
                    act = make_raise(raise_to)

                elif equity >= call_at:
                    act = {"action": "call"}

                else:
                    act = passive()

        return act
    
    except Exception as e:
        print("error: ", repr(e))
        return passive() # passive play in case we fail idk y