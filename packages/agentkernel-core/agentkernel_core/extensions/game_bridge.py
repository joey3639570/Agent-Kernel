"""WebSocket-based Game AI Bridge for Unity/Unreal integration.

This module provides a WebSocket server that allows game engines to
communicate with Agent-Kernel for NPC behavior computation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GameActionType(str, Enum):
    """Types of actions an agent can perform in a game."""

    MOVE = "move"
    TALK = "talk"
    ATTACK = "attack"
    INTERACT = "interact"
    WAIT = "wait"
    EMOTE = "emote"
    CUSTOM = "custom"


class GameEventType(str, Enum):
    """Types of events received from the game."""

    AGENT_SPAWN = "agent_spawn"
    AGENT_DESPAWN = "agent_despawn"
    PLAYER_ACTION = "player_action"
    ENVIRONMENT_CHANGE = "environment_change"
    AGENT_PERCEPTION = "agent_perception"
    TICK = "tick"
    CUSTOM = "custom"


class GameState(BaseModel):
    """Snapshot of the game world state.

    Attributes:
        tick: Current game tick.
        timestamp: Wall-clock timestamp.
        agents: Dictionary of agent states keyed by ID.
        players: Dictionary of player states keyed by ID.
        environment: Environment state data.
        custom_data: Additional game-specific data.
    """

    tick: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    agents: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    players: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    environment: Dict[str, Any] = Field(default_factory=dict)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class GameAction(BaseModel):
    """An action to be performed by an agent in the game.

    Attributes:
        agent_id: The agent performing the action.
        action_type: Type of action.
        target: Optional target of the action.
        parameters: Action-specific parameters.
        priority: Action priority (higher = more important).
    """

    agent_id: str
    action_type: GameActionType
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class GameEvent(BaseModel):
    """An event received from the game.

    Attributes:
        event_type: Type of event.
        source: Source of the event (agent/player/system).
        target: Target of the event (if applicable).
        data: Event-specific data.
        tick: Game tick when event occurred.
    """

    event_type: GameEventType
    source: Optional[str] = None
    target: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    tick: int = 0


@dataclass
class GameBridgeConfig:
    """Configuration for the Game Bridge server.

    Attributes:
        host: Server host address.
        port: Server port.
        max_connections: Maximum concurrent game connections.
        heartbeat_interval: Seconds between heartbeat pings.
        action_queue_size: Maximum queued actions per agent.
    """

    host: str = "0.0.0.0"
    port: int = 8765
    max_connections: int = 10
    heartbeat_interval: float = 30.0
    action_queue_size: int = 100


class GameBridge:
    """WebSocket server for game engine integration.

    This class provides:
    - WebSocket server for bidirectional communication
    - Game state synchronization
    - Action dispatching to agents
    - Event handling from game clients
    """

    def __init__(
        self,
        config: Optional[GameBridgeConfig] = None,
        on_event: Optional[Callable[[GameEvent], Coroutine[Any, Any, None]]] = None,
        on_state_update: Optional[Callable[[GameState], Coroutine[Any, Any, None]]] = None,
    ) -> None:
        """Initialize the Game Bridge.

        Args:
            config: Server configuration.
            on_event: Callback for game events.
            on_state_update: Callback for state updates.
        """
        self.config = config or GameBridgeConfig()
        self._on_event = on_event
        self._on_state_update = on_state_update
        self._server: Optional[Any] = None
        self._connections: Set[Any] = set()
        self._game_state = GameState()
        self._action_queues: Dict[str, asyncio.Queue] = {}
        self._running = False

    async def start(self) -> None:
        """Start the WebSocket server."""
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required. Install with: pip install websockets")

        self._running = True
        self._server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port,
            max_size=10 * 1024 * 1024,  # 10MB max message
        )
        logger.info("Game Bridge started on ws://%s:%d", self.config.host, self.config.port)

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        logger.info("Game Bridge stopped")

    async def _handle_connection(self, websocket: Any, path: str) -> None:
        """Handle a new WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            path: The connection path.
        """
        if len(self._connections) >= self.config.max_connections:
            await websocket.close(1013, "Max connections reached")
            return

        self._connections.add(websocket)
        logger.info("Game client connected: %s", websocket.remote_address)

        try:
            # Send initial state
            await self._send_message(websocket, {
                "type": "state_sync",
                "state": self._game_state.model_dump(),
            })

            async for message in websocket:
                await self._handle_message(websocket, message)

        except Exception as e:
            logger.error("Connection error: %s", e)
        finally:
            self._connections.discard(websocket)
            logger.info("Game client disconnected")

    async def _handle_message(self, websocket: Any, message: str) -> None:
        """Handle an incoming message from game client.

        Args:
            websocket: The WebSocket connection.
            message: The raw message string.
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "event":
                event = GameEvent(**data.get("event", {}))
                if self._on_event:
                    await self._on_event(event)

            elif msg_type == "state_update":
                state_data = data.get("state", {})
                self._game_state = GameState(**state_data)
                if self._on_state_update:
                    await self._on_state_update(self._game_state)

            elif msg_type == "request_actions":
                agent_id = data.get("agent_id")
                if agent_id:
                    actions = await self._get_pending_actions(agent_id)
                    await self._send_message(websocket, {
                        "type": "actions",
                        "agent_id": agent_id,
                        "actions": [a.model_dump() for a in actions],
                    })

            elif msg_type == "ping":
                await self._send_message(websocket, {"type": "pong"})

        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON message: %s", e)
        except Exception as e:
            logger.error("Message handling error: %s", e)

    async def _send_message(self, websocket: Any, data: Dict[str, Any]) -> None:
        """Send a message to a game client.

        Args:
            websocket: The WebSocket connection.
            data: Message data to send.
        """
        try:
            await websocket.send(json.dumps(data, default=str))
        except Exception as e:
            logger.error("Failed to send message: %s", e)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcast a message to all connected game clients.

        Args:
            data: Message data to broadcast.
        """
        if not self._connections:
            return

        message = json.dumps(data, default=str)
        await asyncio.gather(
            *[ws.send(message) for ws in self._connections],
            return_exceptions=True,
        )

    async def queue_action(self, action: GameAction) -> None:
        """Queue an action for an agent.

        Args:
            action: The action to queue.
        """
        if action.agent_id not in self._action_queues:
            self._action_queues[action.agent_id] = asyncio.Queue(
                maxsize=self.config.action_queue_size
            )

        queue = self._action_queues[action.agent_id]
        try:
            queue.put_nowait(action)
        except asyncio.QueueFull:
            # Remove oldest action and add new one
            queue.get_nowait()
            queue.put_nowait(action)

    async def _get_pending_actions(self, agent_id: str) -> List[GameAction]:
        """Get and clear pending actions for an agent.

        Args:
            agent_id: The agent ID.

        Returns:
            List of pending actions.
        """
        if agent_id not in self._action_queues:
            return []

        queue = self._action_queues[agent_id]
        actions = []
        while not queue.empty():
            try:
                actions.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        return sorted(actions, key=lambda a: -a.priority)

    def get_game_state(self) -> GameState:
        """Get the current game state.

        Returns:
            Current GameState.
        """
        return self._game_state

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific agent.

        Args:
            agent_id: The agent ID.

        Returns:
            Agent state dict or None.
        """
        return self._game_state.agents.get(agent_id)

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

