from .state import Session, SplitMode


def calculate_split(session: Session) -> str:
    total = session.total
    players = session.players

    if session.mode == SplitMode.EQUAL:
        per_person = total / len(players)
        lines = [
            f"💰 Total: ฿{total:,.2f}",
            f"👥 {len(players)} players — equal split",
            "",
        ]
        for p in players:
            lines.append(f"• {p['name']}: ฿{per_person:,.2f}")
        return "\n".join(lines)

    elif session.mode == SplitMode.HOURS:
        total_hours = sum(p["hours"] for p in players)
        per_hour = total / total_hours
        lines = [
            f"💰 Total: ฿{total:,.2f}",
            f"⏱️ Total hours: {total_hours:.1f}h  (฿{per_hour:,.2f}/hr)",
            "",
        ]
        for p in players:
            amount = p["hours"] * per_hour
            lines.append(f"• {p['name']} ({p['hours']}h): ฿{amount:,.2f}")
        return "\n".join(lines)

    elif session.mode == SplitMode.CUSTOM:
        custom_total = sum(p["amount"] for p in players)
        lines = [f"💰 Total: ฿{total:,.2f}", ""]
        for p in players:
            lines.append(f"• {p['name']}: ฿{p['amount']:,.2f}")
        diff = total - custom_total
        if abs(diff) > 0.01:
            lines.append(
                f"\n⚠️ Amounts sum to ฿{custom_total:,.2f} "
                f"(difference: ฿{diff:+,.2f})"
            )
        else:
            lines.append("\n✅ Amounts balance perfectly!")
        return "\n".join(lines)

    return "Unknown split mode."
