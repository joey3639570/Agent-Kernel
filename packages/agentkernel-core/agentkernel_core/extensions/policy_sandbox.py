"""Policy Sandbox for economic and social simulation.

This module provides schemas and utilities for running policy simulations
with configurable global state and analytics tracking.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GlobalState(BaseModel):
    """Global state parameters for policy simulation.

    Attributes:
        tick: Current simulation tick.
        timestamp: Wall-clock timestamp.
        economic: Economic indicators.
        social: Social indicators.
        policy: Active policy parameters.
        custom: Custom state variables.
    """

    tick: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    economic: Dict[str, float] = Field(default_factory=lambda: {
        "gdp": 1000000.0,
        "inflation_rate": 0.02,
        "unemployment_rate": 0.05,
        "interest_rate": 0.03,
        "tax_rate": 0.25,
        "government_spending": 250000.0,
        "trade_balance": 0.0,
        "consumer_confidence": 0.7,
        "business_confidence": 0.7,
    })
    social: Dict[str, float] = Field(default_factory=lambda: {
        "population": 1000000,
        "happiness_index": 0.65,
        "inequality_gini": 0.35,
        "crime_rate": 0.02,
        "education_index": 0.7,
        "health_index": 0.75,
        "trust_in_government": 0.5,
        "social_mobility": 0.4,
    })
    policy: Dict[str, Any] = Field(default_factory=lambda: {
        "fiscal_policy": "neutral",  # expansionary, neutral, contractionary
        "monetary_policy": "neutral",
        "trade_policy": "open",  # open, protectionist
        "welfare_level": "medium",  # low, medium, high
        "regulation_level": "medium",
    })
    custom: Dict[str, Any] = Field(default_factory=dict)

    def apply_policy_change(self, policy_name: str, new_value: Any) -> None:
        """Apply a policy change and update related indicators.

        Args:
            policy_name: Name of the policy to change.
            new_value: New policy value.
        """
        old_value = self.policy.get(policy_name)
        self.policy[policy_name] = new_value

        # Simple policy effects (in reality, these would be more complex)
        if policy_name == "fiscal_policy":
            if new_value == "expansionary":
                self.economic["government_spending"] *= 1.1
                self.economic["inflation_rate"] += 0.005
            elif new_value == "contractionary":
                self.economic["government_spending"] *= 0.9
                self.economic["inflation_rate"] -= 0.003

        elif policy_name == "tax_rate" and isinstance(new_value, (int, float)):
            change = new_value - self.economic["tax_rate"]
            self.economic["tax_rate"] = new_value
            self.social["trust_in_government"] -= change * 0.5

        logger.info("Policy changed: %s from %s to %s", policy_name, old_value, new_value)


class SimulationMetrics(BaseModel):
    """Metrics tracked during simulation.

    Attributes:
        tick: Simulation tick.
        timestamp: When metrics were recorded.
        gdp: GDP value.
        inflation: Inflation rate.
        unemployment: Unemployment rate.
        happiness: Happiness index.
        inequality: Gini coefficient.
        custom_metrics: Additional tracked metrics.
    """

    tick: int
    timestamp: datetime = Field(default_factory=datetime.now)
    gdp: float = 0.0
    inflation: float = 0.0
    unemployment: float = 0.0
    happiness: float = 0.0
    inequality: float = 0.0
    custom_metrics: Dict[str, float] = Field(default_factory=dict)

    @classmethod
    def from_global_state(cls, state: GlobalState) -> "SimulationMetrics":
        """Create metrics from global state.

        Args:
            state: Current global state.

        Returns:
            SimulationMetrics instance.
        """
        return cls(
            tick=state.tick,
            timestamp=state.timestamp,
            gdp=state.economic.get("gdp", 0),
            inflation=state.economic.get("inflation_rate", 0),
            unemployment=state.economic.get("unemployment_rate", 0),
            happiness=state.social.get("happiness_index", 0),
            inequality=state.social.get("inequality_gini", 0),
        )


class PolicySandbox:
    """Sandbox environment for policy simulation.

    This class provides:
    - Global state management
    - Metrics tracking and export
    - Policy intervention hooks
    - Analytics export (CSV, JSON, Parquet)
    """

    def __init__(
        self,
        initial_state: Optional[GlobalState] = None,
        update_fn: Optional[Callable[[GlobalState], GlobalState]] = None,
    ) -> None:
        """Initialize the policy sandbox.

        Args:
            initial_state: Initial global state.
            update_fn: Function to update state each tick.
        """
        self.state = initial_state or GlobalState()
        self._update_fn = update_fn
        self._metrics_history: List[SimulationMetrics] = []
        self._policy_log: List[Dict[str, Any]] = []
        self._running = False

    def set_update_function(
        self,
        fn: Callable[[GlobalState], GlobalState],
    ) -> None:
        """Set the state update function.

        Args:
            fn: Function that takes current state and returns updated state.
        """
        self._update_fn = fn

    def apply_policy(self, policy_name: str, value: Any) -> None:
        """Apply a policy change.

        Args:
            policy_name: Name of the policy.
            value: New policy value.
        """
        old_value = self.state.policy.get(policy_name)
        self.state.apply_policy_change(policy_name, value)

        self._policy_log.append({
            "tick": self.state.tick,
            "timestamp": datetime.now().isoformat(),
            "policy": policy_name,
            "old_value": old_value,
            "new_value": value,
        })

    def step(self) -> SimulationMetrics:
        """Advance the simulation by one tick.

        Returns:
            Metrics for the current tick.
        """
        # Update tick
        self.state.tick += 1
        self.state.timestamp = datetime.now()

        # Apply update function if provided
        if self._update_fn:
            self.state = self._update_fn(self.state)

        # Record metrics
        metrics = SimulationMetrics.from_global_state(self.state)
        self._metrics_history.append(metrics)

        return metrics

    def run(self, ticks: int) -> List[SimulationMetrics]:
        """Run the simulation for a number of ticks.

        Args:
            ticks: Number of ticks to simulate.

        Returns:
            List of metrics for each tick.
        """
        self._running = True
        results = []

        for _ in range(ticks):
            if not self._running:
                break
            metrics = self.step()
            results.append(metrics)

        self._running = False
        return results

    def stop(self) -> None:
        """Stop the running simulation."""
        self._running = False

    def get_metrics_history(self) -> List[SimulationMetrics]:
        """Get the full metrics history.

        Returns:
            List of all recorded metrics.
        """
        return list(self._metrics_history)

    def get_policy_log(self) -> List[Dict[str, Any]]:
        """Get the policy change log.

        Returns:
            List of policy changes.
        """
        return list(self._policy_log)

    def export_csv(self, include_custom: bool = True) -> str:
        """Export metrics history as CSV.

        Args:
            include_custom: Whether to include custom metrics.

        Returns:
            CSV string.
        """
        if not self._metrics_history:
            return ""

        output = io.StringIO()

        # Determine columns
        base_columns = ["tick", "timestamp", "gdp", "inflation", "unemployment", "happiness", "inequality"]
        custom_columns = []
        if include_custom and self._metrics_history:
            custom_columns = list(self._metrics_history[0].custom_metrics.keys())

        writer = csv.DictWriter(output, fieldnames=base_columns + custom_columns)
        writer.writeheader()

        for metrics in self._metrics_history:
            row = {
                "tick": metrics.tick,
                "timestamp": metrics.timestamp.isoformat(),
                "gdp": metrics.gdp,
                "inflation": metrics.inflation,
                "unemployment": metrics.unemployment,
                "happiness": metrics.happiness,
                "inequality": metrics.inequality,
            }
            if include_custom:
                row.update(metrics.custom_metrics)
            writer.writerow(row)

        return output.getvalue()

    def export_json(self) -> str:
        """Export metrics history as JSON.

        Returns:
            JSON string.
        """
        data = {
            "simulation": {
                "total_ticks": self.state.tick,
                "final_state": self.state.model_dump(),
            },
            "metrics_history": [m.model_dump() for m in self._metrics_history],
            "policy_log": self._policy_log,
        }
        return json.dumps(data, indent=2, default=str)

    def export_parquet(self, filepath: str) -> None:
        """Export metrics history as Parquet file.

        Args:
            filepath: Path to save the Parquet file.

        Raises:
            ImportError: If pandas/pyarrow not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas and pyarrow required. Install with: pip install pandas pyarrow")

        if not self._metrics_history:
            logger.warning("No metrics to export")
            return

        records = [m.model_dump() for m in self._metrics_history]
        df = pd.DataFrame(records)
        df.to_parquet(filepath, index=False)
        logger.info("Exported %d records to %s", len(records), filepath)

    def reset(self, new_state: Optional[GlobalState] = None) -> None:
        """Reset the sandbox to initial state.

        Args:
            new_state: Optional new initial state.
        """
        self.state = new_state or GlobalState()
        self._metrics_history = []
        self._policy_log = []
        self._running = False
        logger.info("Sandbox reset")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the simulation.

        Returns:
            Summary dictionary.
        """
        if not self._metrics_history:
            return {"status": "no_data"}

        first = self._metrics_history[0]
        last = self._metrics_history[-1]

        return {
            "total_ticks": self.state.tick,
            "policy_changes": len(self._policy_log),
            "gdp_change": (last.gdp - first.gdp) / first.gdp if first.gdp else 0,
            "inflation_change": last.inflation - first.inflation,
            "unemployment_change": last.unemployment - first.unemployment,
            "happiness_change": last.happiness - first.happiness,
            "inequality_change": last.inequality - first.inequality,
            "final_state": {
                "gdp": last.gdp,
                "inflation": last.inflation,
                "unemployment": last.unemployment,
                "happiness": last.happiness,
                "inequality": last.inequality,
            },
        }

