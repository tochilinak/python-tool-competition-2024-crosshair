from crosshair.path_cover import *
import signal


class TimeoutException(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutException()


def path_cover(
    ctxfn: FunctionInfo,
    options: AnalysisOptions,
    coverage_type: CoverageType,
    arg_formatter: Callable[[BoundArguments], str] = format_boundargs,
) -> List[PathSummary]:
    
    fn, sig = ctxfn.callable()
    while getattr(fn, "__wrapped__", None):
        # Usually we don't want to run decorator code. (and we certainly don't want
        # to measure coverage on the decorator rather than the real body) Unwrap:
        fn = fn.__wrapped__  # type: ignore
    search_root = RootNode()

    paths: List[PathSummary] = []
    coverage: CoverageTracingModule = CoverageTracingModule(fn)

    def run_path(args: BoundArguments):
        nonlocal coverage
        with NoTracing():
            coverage = CoverageTracingModule(fn)
        with PushedModule(coverage):
            return fn(*args.args, **args.kwargs)

    def on_path_complete(
        space: StateSpace,
        pre_args: BoundArguments,
        post_args: BoundArguments,
        ret,
        exc: Optional[BaseException],
        exc_stack: Optional[traceback.StackSummary],
    ) -> bool:
        with ExceptionFilter() as efilter:
            space.detach_path()

            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(1)  # terminate execution after 1 second

            try:
                reprer = context_statespace().extra(LazyCreationRepr)
                formatted_pre_args = reprer.eval_friendly_format(pre_args, arg_formatter)

                pre_args = deep_realize(pre_args)
                post_args = deep_realize(post_args)
                ret = reprer.eval_friendly_format(ret, lambda x: builtins.repr(x))
                references = reprer.repr_references

                cov = coverage.get_results(fn)
                if exc is not None:
                    debug(
                        "user-level exception found", type(exc), exc, test_stack(exc_stack)
                    )
                    exc_message = realize(str(exc)) if len(exc.args) > 0 else None
                    paths.append(
                        PathSummary(
                            pre_args,
                            formatted_pre_args,
                            ret,
                            type(exc),
                            exc_message,
                            post_args,
                            cov,
                            references,
                        )
                    )
                else:
                    paths.append(
                        PathSummary(
                            pre_args,
                            formatted_pre_args,
                            ret,
                            None,
                            None,
                            post_args,
                            cov,
                            references,
                        )
                    )
                signal.alarm(0)
                return False
            except TimeoutException:
                print("Raised TimeoutException during serialization")
                signal.alarm(0)
                return False
        debug("Skipping path (failed to realize values)", efilter.user_exc)
        signal.alarm(0)
        return False

    explore_paths(run_path, sig, options, search_root, on_path_complete)

    opcodes_found: Set[int] = set()
    selected: List[PathSummary] = []
    while paths:
        next_best = max(
            paths, key=lambda p: len(p.coverage.offsets_covered - opcodes_found)
        )
        cur_offsets = next_best.coverage.offsets_covered
        if coverage_type == CoverageType.OPCODE:
            debug("Next best path covers these opcode offsets:", cur_offsets)
            if len(cur_offsets - opcodes_found) == 0:
                break
        selected.append(next_best)
        opcodes_found |= cur_offsets
        paths = [p for p in paths if p is not next_best]
    return selected


import crosshair.path_cover
crosshair.path_cover = path_cover
