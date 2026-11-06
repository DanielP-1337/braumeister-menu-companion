"""Recipe picker parsing without loading Home Assistant."""
import ast
from pathlib import Path

import pytest

source = Path(__file__).parents[1] / "custom_components/braumeister_menu/__init__.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "recipe_picker")
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
picker = namespace["recipe_picker"]


def device(count, slot):
    fields = ["0"] * 16
    fields[3], fields[8], fields[9] = "2015", str(count), str(slot)
    recipes = ["header"] + ["X".join([str(i)] + ["0"] * 19) + f".Recipe {i + 1};" for i in range(10)]
    return {"bm_stat": "FW;TEST;1;" + "X".join(fields), "rz": "\n".join(recipes)}


@pytest.mark.parametrize("count", range(1, 10))
def test_all_live_slots_and_no_stale_extra_entries(count):
    for slot in range(count):
        result = picker(device(count, slot))
        assert result == {"slot": slot, "recipes": {str(i): f"Recipe {i + 1}" for i in range(count)}}


@pytest.mark.parametrize("count,slot", [(0, 0), (10, 0), (9, 9), (4, 4), (9, -1), ("bad", 0)])
def test_invalid_count_or_selection(count, slot):
    assert picker(device(count, slot)) is None
