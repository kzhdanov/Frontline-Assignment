"""Pipecat schemas built from dependency-free canonical tool contracts."""

from pipecat.adapters.schemas.function_schema import FunctionSchema

from tool_contracts import TOOL_CONTRACTS


def _schema(name: str) -> FunctionSchema:
    contract = TOOL_CONTRACTS[name]
    return FunctionSchema(name=name, description=contract["description"], properties=contract["properties"], required=contract["required"])


VERIFY_CARRIER_FUNCTION = _schema("verify_carrier")
GET_LOAD_CONTEXT_FUNCTION = _schema("get_load_context")
RECORD_AGREEMENT_FUNCTION = _schema("record_agreement")
END_CALL_FUNCTION = _schema("end_call")
TRANSFER_TO_HUMAN_FUNCTION = _schema("transfer_to_human")
TRANSFER_HUMAN_TO_CARRIER_FUNCTION = _schema("transfer_human_to_carrier")
