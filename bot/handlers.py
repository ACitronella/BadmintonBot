from .state import Session, SplitMode, State, get_session, reset_session
from .bill_splitter import calculate_split

HELP_TEXT = (
    "🏸 Badminton Bill Splitter\n\n"
    "Commands:\n"
    "• new — Start a new bill split\n"
    "• cancel — Cancel current session\n"
    "• help — Show this message\n\n"
    "Split modes:\n"
    "1️⃣ Equal — Divide evenly among players\n"
    "2️⃣ Hours — Each pays by hours played\n"
    "3️⃣ Custom — Set each person's amount manually"
)

_TRIGGER_WORDS = {"new", "เริ่ม", "start", "cancel", "ยกเลิก", "stop", "help", "?", "ช่วยด้วย"}


def handle_message(source_id: str, text: str) -> str:
    text = text.strip()
    lower = text.lower()
    session = get_session(source_id)

    # Global commands always work regardless of state
    if lower in {"new", "เริ่ม", "start"}:
        session = reset_session(source_id)
        session.state = State.AWAITING_TOTAL
        return (
            "🏸 Badminton Bill Splitter\n\n"
            "What is the total court rental cost? (THB)\n"
            "e.g. 600"
        )

    if lower in {"cancel", "ยกเลิก", "stop"}:
        reset_session(source_id)
        return "❌ Cancelled. Type 'new' to start a new split."

    if lower in {"help", "?", "ช่วยด้วย"}:
        return HELP_TEXT

    # When idle and no command matched, prompt to start
    if session.state == State.IDLE:
        return "Type 'new' to start splitting a bill! 🏸"

    if session.state == State.AWAITING_TOTAL:
        return _handle_total(session, text)

    if session.state == State.AWAITING_MODE:
        return _handle_mode(session, text)

    if session.state == State.AWAITING_PLAYER_COUNT:
        return _handle_player_count(session, text)

    if session.state == State.AWAITING_PLAYERS:
        return _handle_player_input(session, source_id, text)

    return "Type 'help' for available commands."


def _handle_total(session: Session, text: str) -> str:
    try:
        total = float(text.replace(",", "").replace("฿", "").strip())
        if total <= 0:
            return "❌ Please enter a positive amount."
        session.total = total
        session.state = State.AWAITING_MODE
        return (
            f"✅ Total: ฿{total:,.2f}\n\n"
            "How would you like to split the bill?\n"
            "1️⃣ Equal split\n"
            "2️⃣ By hours played\n"
            "3️⃣ Custom amounts\n\n"
            "Reply with 1, 2, or 3"
        )
    except ValueError:
        return "❌ Please enter a valid number. e.g. 600"


def _handle_mode(session: Session, text: str) -> str:
    mode_map = {
        "1": SplitMode.EQUAL,
        "equal": SplitMode.EQUAL,
        "2": SplitMode.HOURS,
        "hours": SplitMode.HOURS,
        "hour": SplitMode.HOURS,
        "3": SplitMode.CUSTOM,
        "custom": SplitMode.CUSTOM,
    }
    mode = mode_map.get(text.lower())
    if not mode:
        return "❌ Please reply with 1, 2, or 3."
    session.mode = mode
    session.state = State.AWAITING_PLAYER_COUNT
    return "How many players? e.g. 4"


def _handle_player_count(session: Session, text: str) -> str:
    try:
        n = int(text.strip())
        if n < 1:
            return "❌ Must have at least 1 player."
        if n > 20:
            return "❌ Maximum 20 players supported."
        session.n_players = n
        session.players = []
        session.state = State.AWAITING_PLAYERS
        return _next_player_prompt(session)
    except ValueError:
        return "❌ Please enter a whole number. e.g. 4"


def _handle_player_input(session: Session, source_id: str, text: str) -> str:
    player_num = len(session.players) + 1

    if session.mode == SplitMode.EQUAL:
        name = text.strip()
        if not name:
            return f"❌ Please enter a name for player {player_num}."
        session.players.append({"name": name})

    elif session.mode == SplitMode.HOURS:
        parts = text.rsplit(" ", 1)
        if len(parts) != 2:
            return f"❌ Please enter name and hours.\ne.g. John 2.5"
        try:
            hours = float(parts[1])
            if hours <= 0:
                return "❌ Hours must be greater than 0."
            session.players.append({"name": parts[0].strip(), "hours": hours})
        except ValueError:
            return f"❌ Please enter name and hours.\ne.g. John 2.5"

    elif session.mode == SplitMode.CUSTOM:
        parts = text.rsplit(" ", 1)
        if len(parts) != 2:
            return f"❌ Please enter name and amount.\ne.g. John 200"
        try:
            amount = float(parts[1].replace(",", "").replace("฿", ""))
            if amount < 0:
                return "❌ Amount cannot be negative."
            session.players.append({"name": parts[0].strip(), "amount": amount})
        except ValueError:
            return f"❌ Please enter name and amount.\ne.g. John 200"

    if len(session.players) >= session.n_players:
        summary = calculate_split(session)
        reset_session(source_id)
        return f"📊 Bill Summary\n\n{summary}\n\nType 'new' to split another bill!"

    return _next_player_prompt(session)


def _next_player_prompt(session: Session) -> str:
    player_num = len(session.players) + 1
    total = session.n_players
    if session.mode == SplitMode.EQUAL:
        return f"Player {player_num}/{total} — enter name:"
    elif session.mode == SplitMode.HOURS:
        return f"Player {player_num}/{total} — enter name and hours:\ne.g. John 2.5"
    else:
        return f"Player {player_num}/{total} — enter name and amount:\ne.g. John 200"
