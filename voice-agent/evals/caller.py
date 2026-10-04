from __future__ import annotations

from .scenario import Scenario


class Zone2Caller:
    """Deterministic caller; advances by completed agent speech turns."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.after_load_turn = 0
        self.identity_supplied = False
        self.reference_supplied = False

    def next_message(self, *, load_loaded: bool, tool_names: list[str]) -> str:
        if "verify_carrier" not in tool_names:
            self.identity_supplied = True
            return f"Hi, my MC number is {self.scenario.carrier['mc_number']}."
        if not load_loaded:
            self.reference_supplied = True
            return f"Yes, that's us. I'm calling about reference {self.scenario.load['id']}."

        replies = [
            f"I need ${self.scenario.carrier_offer:,.0f} for that load.",
            f"No, I can't do that. I still need ${self.scenario.carrier_offer:,.0f}.",
            f"I can come down to ${self.scenario.settlement_offer:,.0f}.",
            f"Yes, we have a deal at ${self.scenario.settlement_offer:,.0f}.",
            f"This is {self.scenario.contact['name']}, and my phone is {self.scenario.contact['phone']}.",
            "Thanks, that works. Goodbye.",
        ]
        index = min(self.after_load_turn, len(replies) - 1)
        self.after_load_turn += 1
        return replies[index]

