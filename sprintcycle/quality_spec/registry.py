from typing import Any, Dict, List, Optional


class QualityRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, Any] = {}
        self._providers: Dict[str, Any] = {}
        self._rules: Dict[str, Any] = {}
        self._plugins: Dict[str, Any] = {}

    def register_adapter(self, adapter: Any) -> None:
        name = getattr(adapter, "name", None) or adapter.__class__.__name__.lower()
        self._adapters[name] = adapter

    def register_provider(self, provider: Any) -> None:
        name = getattr(provider, "name", None) or provider.__class__.__name__.lower()
        self._providers[name] = provider

    def register_rule(self, rule: Any) -> None:
        rule_id = getattr(rule, "id", None)
        if not rule_id:
            raise ValueError("rule id is required")
        self._rules[rule_id] = rule

    def register_plugin(self, plugin: Any) -> None:
        name = getattr(plugin, "name", None) or plugin.__class__.__name__.lower()
        self._plugins[name] = plugin

    def get_adapter(self, name: str) -> Optional[Any]:
        return self._adapters.get(name)

    def get_provider(self, name: str) -> Optional[Any]:
        return self._providers.get(name)

    def get_rule(self, rule_id: str) -> Optional[Any]:
        return self._rules.get(rule_id)

    def list_adapters(self) -> List[Any]:
        return list(self._adapters.values())

    def list_providers(self) -> List[Any]:
        return list(self._providers.values())

    def list_rules(self) -> List[Any]:
        return list(self._rules.values())

    def for_gate(self, gate: str) -> Dict[str, Any]:
        rules = []
        for rule in self._rules.values():
            applies = getattr(rule, "applies_to", [])
            if not applies or gate in applies:
                rules.append(rule)
        return {
            "adapters": self.list_adapters(),
            "providers": self.list_providers(),
            "rules": rules,
            "plugins": list(self._plugins.values()),
        }
