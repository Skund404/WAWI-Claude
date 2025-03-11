# gui/utils/event_bus.py
"""
Event bus for communication between GUI components.
Provides a simple publish-subscribe mechanism.
"""

import logging
from typing import Any, Callable, Dict, List, Set

logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple event bus implementation for GUI component communication.
    Uses a publish-subscribe pattern.
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._topic_registry: Set[str] = set()

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: The topic to subscribe to
            callback: The callback function to call when the topic is published
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        self._topic_registry.add(topic)
        logger.debug(f"Subscribed to topic: {topic}")

    def unsubscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from a topic.

        Args:
            topic: The topic to unsubscribe from
            callback: The callback function to remove
        """
        if topic in self._subscribers and callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
            logger.debug(f"Unsubscribed from topic: {topic}")
            # Remove topic if no subscribers left
            if not self._subscribers[topic]:
                del self._subscribers[topic]

    def publish(self, topic: str, data: Any = None) -> None:
        """
        Publish data to a topic.

        Args:
            topic: The topic to publish to
            data: The data to publish
        """
        if topic in self._subscribers:
            logger.debug(f"Publishing to topic: {topic}")
            for callback in self._subscribers[topic]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler for topic {topic}: {str(e)}")

    def register_topic(self, topic: str) -> None:
        """
        Register a topic.

        Args:
            topic: The topic to register
        """
        self._topic_registry.add(topic)

    def get_topics(self) -> List[str]:
        """
        Get all registered topics.

        Returns:
            List of registered topics
        """
        return list(self._topic_registry)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscribers.clear()
        logger.debug("Event bus cleared")


# Global event bus instance
_event_bus = EventBus()


# Public functions to interact with the global event bus
def subscribe(topic: str, callback: Callable[[Any], None]) -> None:
    """
    Subscribe to a topic on the global event bus.

    Args:
        topic: The topic to subscribe to
        callback: The callback function to call when the topic is published
    """
    _event_bus.subscribe(topic, callback)


def unsubscribe(topic: str, callback: Callable[[Any], None]) -> None:
    """
    Unsubscribe from a topic on the global event bus.

    Args:
        topic: The topic to unsubscribe from
        callback: The callback function to remove
    """
    _event_bus.unsubscribe(topic, callback)


def publish(topic: str, data: Any = None) -> None:
    """
    Publish data to a topic on the global event bus.

    Args:
        topic: The topic to publish to
        data: The data to publish
    """
    _event_bus.publish(topic, data)


def register_topic(topic: str) -> None:
    """
    Register a topic on the global event bus.

    Args:
        topic: The topic to register
    """
    _event_bus.register_topic(topic)


def get_topics() -> List[str]:
    """
    Get all registered topics from the global event bus.

    Returns:
        List of registered topics
    """
    return _event_bus.get_topics()


def clear() -> None:
    """Clear all subscriptions from the global event bus."""
    _event_bus.clear()