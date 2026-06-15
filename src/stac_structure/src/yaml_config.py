"""Configuration helpers for YAML configuration files."""

import logging
import os
import re
from typing import IO, Any

import yaml  

LOGGER = logging.getLogger(__name__)


# --- General helpers for YAML files ---
def get_typed_value(value: str) -> float | int | str:
    """
    YAML loader natively loads all values as strings. This function maps values to
    native python data types (int, float, str).
    - If value contains a dot (.) --> map to float.
    - If value starts with a 0 and is longer than 1 char --> keep as string.
    - Else try to map to int, if fails keep as string.
    (source: https://github.com/geopython/pygeoapi/blob/master/pygeoapi/util.py)

    :param value: yamlvalue
    :return: yaml value as a native Python data type (str, int, float)
    """

    value2: float | int | str

    try:
        if "." in value:
            value2 = float(value)
        elif len(value) > 1 and value.startswith("0"):
            value2 = value
        else:
            value2 = int(value)
    except ValueError:
        value2 = value

    return value2


def yaml_load(fh: IO[str]) -> dict[str, Any]:
    """
    Load YAML file into a dict with support for environment variables inside the YAML file
    (e.g. path: ${HOME}/data).
    (source: https://github.com/geopython/pygeoapi/blob/master/pygeoapi/util.py)

    :param fh: file handle
    :return: dict representation of YAML
    """

    path_matcher = re.compile(r".*\$\{([^}^{]+)\}.*")

    def path_constructor(
        _loader: yaml.SafeLoader, node: yaml.Node
    ) -> float | int | str:
        match = path_matcher.match(node.value)
        if match is None:
            msg = "Invalid environment-variable expression in config"
            raise EnvironmentError(msg)

        env_var = match.group(1)
        if env_var not in os.environ:
            msg = f"Undefined environment variable {env_var} in config"
            raise EnvironmentError(msg)
        return get_typed_value(os.path.expandvars(node.value))

    class EnvVarLoader(yaml.SafeLoader):
        pass

    EnvVarLoader.add_implicit_resolver("!path", path_matcher, None)
    EnvVarLoader.add_constructor("!path", path_constructor)

    return yaml.load(fh, Loader=EnvVarLoader)


def read_yml_config(conf_file: str | os.PathLike[str]) -> dict[str, Any]:
    """
    Reads a YAML configuration file and returns its contents as a dictionary.

    :param conf_file: Path to the YAML config file `<name>.yaml`.
    :return: Configuration dictionary.
    """
    if not os.path.exists(conf_file):
        raise FileNotFoundError(f"Config file not found: {conf_file}")
    with open(conf_file, "r", encoding="utf-8") as fh:
        config = yaml_load(fh)
    return config

def _normalize_config_values(value: Any) -> Any:
    """Trim strings recursively and normalize null/boolean tokens."""
    if isinstance(value, dict):
        return {k: _normalize_config_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_config_values(v) for v in value]
    if isinstance(value, str):
        cleaned = value.rstrip() if "\n" in value else value.strip()
        low = cleaned.lower()
        if low in {"none", "null", "~"}:
            return None
        if low == "true":
            return True
        if low == "false":
            return False
        return cleaned
    return value


def iter_map_service_layer_entries(
    config: dict[str, Any] | None,
) -> list[tuple[str, dict[str, Any]]]:
    """Return top-level entries except 'map' that are dicts."""
    if not isinstance(config, dict):
        return []
    return [(k, v) for k, v in config.items() if k != "map" and isinstance(v, dict)]


def load_map_service_config(
    conf_file: str | os.PathLike[str],
) -> tuple[dict[str, Any], dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    """Load config and split into map + layer entries."""
    config = _normalize_config_values(read_yml_config(conf_file))
    config_map = config.get("map", {}) if isinstance(config, dict) else {}
    if not isinstance(config_map, dict):
        config_map = {}
    config_layers = iter_map_service_layer_entries(config)
    return config, config_map, config_layers


def feature_class_layers(
    config_layers: list[tuple[str, dict[str, Any]]],
) -> list[tuple[str, dict[str, Any]]]:
    """Filter layer entries to type=feature_class."""
    out: list[tuple[str, dict[str, Any]]] = []
    for name, layer_cfg in config_layers:
        if str(layer_cfg.get("type", "")).strip().lower() == "feature_class":
            out.append((name, layer_cfg))
    return out