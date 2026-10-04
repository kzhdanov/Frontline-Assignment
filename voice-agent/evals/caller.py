from __future__ import annotations

from .amounts import extract_rate_amounts
from .scenario import Scenario


class Zone2Caller:
    """Deterministic caller that advances only on recognizable agent actions."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.negotiation_state = "offer"
        self.identity_supplied = False
        self.reference_supplied = False

    def next_message(self, *, assistant_text: str, carrier_verified: bool, load_loaded: bool) -> str:
        if not carrier_verified:
            self.identity_supplied = True
            return f"Hi, my MC number is {self.scenario.carrier['mc_number']}."
        if not load_loaded:
            self.reference_supplied = True
            return f"Yes, that's us. I'm calling about reference {self.scenario.load['id']}."

        lowered = assistant_text.lower()
        rates = extract_rate_amounts(assistant_text)
        if self.negotiation_state == "offer":
            self.negotiation_state = "first_counter"
            return f"I need ${self.scenario.carrier_offer:,.0f} for that load."
        if self.negotiation_state == "first_counter" and rates:
            self.negotiation_state = "second_counter"
            return f"No, I can't do that. I still need ${self.scenario.carrier_offer:,.0f}."
        if self.negotiation_state == "second_counter" and rates:
            self.negotiation_state = "confirmation"
            return f"I can come down to ${self.scenario.settlement_offer:,.0f}."
        if self.negotiation_state == "confirmation" and rates and any(
            word in lowered for word in ("confirm", "deal", "agree", "work")
        ):
            self.negotiation_state = "contact"
            return f"Yes, we have a deal at ${self.scenario.settlement_offer:,.0f}."
        if self.negotiation_state == "contact" and any(
            word in lowered for word in ("contact", "name", "phone", "number")
        ):
            self.negotiation_state = "complete"
            return f"This is {self.scenario.contact['name']}, and my phone is {self.scenario.contact['phone']}."
        if self.negotiation_state == "complete":
            return "Thanks, that works. Goodbye."
        return "Could you repeat that for me?"
