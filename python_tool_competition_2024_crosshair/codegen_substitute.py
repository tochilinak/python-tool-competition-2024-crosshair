from crosshair.path_cover import *
import ast


def output_pytest_paths(
    fn: Callable, paths: List[PathSummary]
) -> Tuple[Set[str], List[str]]:
    fn_name = fn.__qualname__
    lines: List[str] = []
    references = {ReferencedIdentifier(fn.__module__, fn_name)}
    imports: Set[str] = set()

    name_with_underscores = fn_name.replace(".", "_")
    for idx, path in enumerate(paths):
        test_name_suffix = "" if idx == 0 else "_" + str(idx + 1)
        exec_fn = f"{fn_name}({path.formatted_args})"
        cur_lines = []
        cur_lines.append(f"def test_{name_with_underscores}{test_name_suffix}():")
        if path.exc is None:
            cur_lines.append(f"    {exec_fn}")
        else:
            imports.add("import pytest")
            if path.exc_message is not None:
                cur_lines.append(
                    f"    with pytest.raises({name_of_type(path.exc)}):"
                )
            else:
                cur_lines.append(f"    with pytest.raises({name_of_type(path.exc)}):")
            cur_lines.append(f"        {exec_fn}")
        cur_lines.append("")
        try:
            ast.parse("\n".join(cur_lines))
            lines += cur_lines
        except SyntaxError:
            None
        references |= path.references
    imports |= import_statements_for_references(references)
    return (imports, lines)


import crosshair.path_cover

crosshair.path_cover.output_pytest_paths = output_pytest_paths
