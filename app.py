
from flask import Flask, render_template, request, redirect, url_for, session
import os
import math

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "dev-only-change-this-key"
)

SPORTS = [
    "Football", "Cricket", "Volleyball", "Basketball",
    "Table Tennis", "Badminton", "Other"
]


def build_knockout(teams, winners):
    """Build rounds and advance selected winners automatically."""
    total = len(teams)
    size = 2 ** math.ceil(math.log2(total))
    byes = size - total

    # Seed teams so byes are handled in the first round.
    seeded = teams[:]
    first_round = []

    for i in range(size // 2):
        if i < byes:
            first_round.append((seeded[i], None))
        else:
            index = byes + 2 * (i - byes)
            if index + 1 < total:
                first_round.append(
                    (seeded[index], seeded[index + 1])
                )

    # If there are no byes, use the original order in pairs.
    if byes == 0:
        first_round = [
            (teams[i], teams[i + 1])
            for i in range(0, total, 2)
        ]

    rounds = []
    current = first_round
    match_number = 1
    round_number = 1

    while current:
        round_matches = []
        next_round = []

        for team1, team2 in current:
            if team2 is None:
                next_round.append(team1)
                continue

            selected = winners.get(str(match_number))
            if selected not in (team1, team2):
                selected = None

            round_matches.append({
                "match": match_number,
                "round": round_number,
                "team1": team1,
                "team2": team2,
                "winner": selected
            })

            next_round.append(
                selected if selected
                else f"Winner of Match {match_number}"
            )
            match_number += 1

        if round_matches:
            rounds.append(round_matches)

        if len(next_round) <= 1:
            break

        current = [
            (next_round[i], next_round[i + 1])
            for i in range(0, len(next_round), 2)
        ]
        round_number += 1

    return rounds


def build_round_robin(teams):
    fixtures = []
    number = 1

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            fixtures.append({
                "match": number,
                "team1": teams[i],
                "team2": teams[j]
            })
            number += 1

    return fixtures


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("tournament_name", "").strip()
        sport = request.form.get("sport", "Football")
        fmt = request.form.get("tournament_type", "knockout")
        raw = request.form.get("teams", "")

        teams = [t.strip() for t in raw.splitlines() if t.strip()]

        if not name:
            session["error"] = "Enter a tournament name."
        elif sport not in SPORTS:
            session["error"] = "Choose a valid sport."
        elif fmt not in ("knockout", "round_robin"):
            session["error"] = "Choose a valid format."
        elif not 2 <= len(teams) <= 32:
            session["error"] = "Enter between 2 and 32 teams."
        elif len({t.casefold() for t in teams}) != len(teams):
            session["error"] = "Team names must be unique."
        elif any(len(t) > 60 for t in teams):
            session["error"] = "Team names must be 60 characters or fewer."
        else:
            session["tournament"] = {
                "name": name,
                "sport": sport,
                "format": fmt,
                "teams": teams
            }
            session["winners"] = {}
            session.pop("error", None)

        return redirect(url_for("home"))

    tournament = session.get("tournament")
    winners = session.get("winners", {})
    error = session.pop("error", None)
    rounds = []
    fixtures = []
    champion = None

    if tournament:
        if tournament["format"] == "knockout":
            rounds = build_knockout(tournament["teams"], winners)

            # Champion exists only when every required match is decided.
            if rounds and rounds[-1]:
                final = rounds[-1][0]
                champion = final["winner"]
        else:
            fixtures = build_round_robin(tournament["teams"])

    return render_template(
        "index.html",
        tournament=tournament,
        rounds=rounds,
        fixtures=fixtures,
        winners=winners,
        champion=champion,
        error=error
    )


@app.route("/winner", methods=["POST"])
def save_winner():
    tournament = session.get("tournament")

    if not tournament or tournament["format"] != "knockout":
        return redirect(url_for("home"))

    match = request.form.get("match", "")
    winner = request.form.get("winner", "")
    rounds = build_knockout(
        tournament["teams"], session.get("winners", {})
    )

    valid_match = None
    for round_matches in rounds:
        for fixture in round_matches:
            if str(fixture["match"]) == match:
                valid_match = fixture
                break

    if valid_match and winner in (
        valid_match["team1"], valid_match["team2"]
    ):
        selections = dict(session.get("winners", {}))
        selections[match] = winner

        # Clear later results because their matchups may have changed.
        for round_matches in rounds:
            for fixture in round_matches:
                if fixture["match"] > int(match):
                    selections.pop(str(fixture["match"]), None)

        session["winners"] = selections

    return redirect(url_for("home"))


@app.route("/reset", methods=["POST"])
def reset():
    session.pop("tournament", None)
    session.pop("winners", None)
    session.pop("error", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
