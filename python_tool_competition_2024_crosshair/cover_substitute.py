from crosshair.main import *
from python_tool_competition_2024_crosshair.path_cover_substitute import path_cover


def cover(
    args: argparse.Namespace, options: AnalysisOptions, stdout: TextIO, stderr: TextIO
) -> int:
    entities = checked_load(args.target, stderr)
    if isinstance(entities, int):
        return entities
    to_be_processed = deque(entities)
    fns = []
    while to_be_processed:
        entity = to_be_processed.pop()
        if isinstance(entity, ModuleType):
            to_be_processed.extend(
                v for k, v in get_top_level_classes_and_functions(entity)
            )
        elif isinstance(entity, FunctionInfo):
            fns.append(entity)
        else:
            assert isinstance(entity, type)
            fns.extend(
                FunctionInfo.from_class(entity, e.__name__)
                for e in entity.__dict__.values()
                if callable(e)
            )

    if not fns:
        print("No functions or methods found.", file=stderr)
        return 2

    options.per_condition_timeout /= len(fns)
    example_output_format = args.example_output_format
    options.stats = Counter()
    imports, lines = set(), []
    for ctxfn in fns:
        pair = ctxfn.get_callable()
        if pair is None:
            continue
        fn = pair[0]

        try:
            paths = path_cover(
                ctxfn,
                options,
                args.coverage_type,
                arg_formatter=format_boundargs_as_dictionary
                if example_output_format == ExampleOutputFormat.ARG_DICTIONARY
                else format_boundargs,
            )
        except NotDeterministic:
            print(
                "Repeated executions are not behaving deterministically.", file=stderr
            )
            if not in_debug():
                print("Re-run in verbose mode for debugging information.", file=stderr)
            return 2
        if example_output_format == ExampleOutputFormat.ARG_DICTIONARY:
            output_argument_dictionary_paths(fn, paths, stdout, stderr)
        elif example_output_format == ExampleOutputFormat.EVAL_EXPRESSION:
            output_eval_exression_paths(fn, paths, stdout, stderr)
        elif example_output_format == ExampleOutputFormat.PYTEST:
            (cur_imports, cur_lines) = output_pytest_paths(fn, paths)
            imports |= cur_imports
            # imports.add(f"import {fn.__qualname__}")
            lines.extend(cur_lines)
        else:
            assert False, "unexpected output format"
    if example_output_format == ExampleOutputFormat.PYTEST:
        stdout.write("\n".join(sorted(imports) + [""] + lines) + "\n")
        stdout.flush()

    return 0


import crosshair.main

crosshair.main.cover = cover
