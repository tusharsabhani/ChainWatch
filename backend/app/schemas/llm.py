from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.chat import ChatContextScope


class ChatToolName(StrEnum):
    EXTERNAL_RISK = "external_risk"
    DEMAND = "demand"
    INVENTORY = "inventory"
    FULFILLMENT = "fulfillment"


class ChatToolDefinition(BaseModel):
    name: ChatToolName
    purpose: str
    supported_scopes: list[ChatContextScope] = Field(default_factory=list)
    cues: list[str] = Field(default_factory=list)


class ChatToolSelection(BaseModel):
    tool_name: ChatToolName
    reason: str


class ChatToolPlan(BaseModel):
    selected_tools: list[ChatToolSelection] = Field(default_factory=list)
    routing_notes: str = "No routing notes were provided."


def default_chat_tools() -> list[ChatToolDefinition]:
    return [
        ChatToolDefinition(
            name=ChatToolName.EXTERNAL_RISK,
            purpose=(
                "Use for country, supplier, tariff, customs, port, route, shipping, freight, strike, "
                "weather, and disruption questions tied to external events."
            ),
            supported_scopes=[
                ChatContextScope.GLOBAL,
                ChatContextScope.PRODUCT,
                ChatContextScope.SUPPLIER,
                ChatContextScope.COUNTRY,
            ],
            cues=[
                "country exposure",
                "supplier disruption",
                "customs bottleneck",
                "tariff pressure",
                "port congestion",
                "route disruption",
                "trade risk",
                "weather impact",
            ],
        ),
        ChatToolDefinition(
            name=ChatToolName.DEMAND,
            purpose=(
                "Use for sell-through, seasonality, demand forecasting, demand spikes, promo lift, "
                "and product velocity questions."
            ),
            supported_scopes=[
                ChatContextScope.GLOBAL,
                ChatContextScope.PRODUCT,
            ],
            cues=[
                "sell through",
                "seasonality",
                "forecast pressure",
                "velocity shift",
                "promo lift",
                "demand outlook",
            ],
        ),
        ChatToolDefinition(
            name=ChatToolName.INVENTORY,
            purpose=(
                "Use for stock levels, replenishment, days of cover, safety stock, reorder urgency, "
                "and stockout risk questions."
            ),
            supported_scopes=[
                ChatContextScope.GLOBAL,
                ChatContextScope.PRODUCT,
            ],
            cues=[
                "stockout risk",
                "replenishment gap",
                "days of cover",
                "safety stock",
                "reorder urgency",
                "buffer health",
            ],
        ),
        ChatToolDefinition(
            name=ChatToolName.FULFILLMENT,
            purpose=(
                "Use for SLA health, on-time delivery, shipment delays, warehouse backlog, carrier issues, "
                "and service-level risk questions."
            ),
            supported_scopes=[
                ChatContextScope.GLOBAL,
                ChatContextScope.PRODUCT,
            ],
            cues=[
                "service level risk",
                "on time rate",
                "shipment delays",
                "warehouse backlog",
                "carrier issue",
                "delivery pressure",
            ],
        ),
    ]
