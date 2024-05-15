"""A test generator using CrossHair."""
import python_tool_competition_2024_crosshair.codegen_substitute
#import python_tool_competition_2024_crosshair.solver_substitute
import python_tool_competition_2024_crosshair.cover_substitute

from io import StringIO
import sys
import time
import traceback
from python_tool_competition_2024.generation_results import (
    FailureReason,
    TestGenerationFailure,
    TestGenerationResult,
    TestGenerationSuccess,
)
from python_tool_competition_2024.generators import FileInfo, TestGenerator
from crosshair.main import cover, command_line_parser
from crosshair.options import DEFAULT_OPTIONS, AnalysisOptionSet
from crosshair.util import set_debug


GENERATION_TIMES: list[float] = []


class CrosshairTestGenerator(TestGenerator):
    """A test generator using CrossHair."""

    def build_test(self, target_file_info: FileInfo) -> TestGenerationResult:
        """
        Genereate a test for the specific target file.

        Args:
            target_file: The `FileInfo` of the file to generate a test for.

        Returns:
            Either a `TestGenerationSuccess` if it was successful, or a
            `TestGenerationFailure` otherwise.
        """

        retcode = 0
        print("Working on", target_file_info.module_name)
        try:
            stdout, stderr = StringIO(), StringIO()
            args = command_line_parser().parse_args([
                "cover",
                "--verbose",
                "--coverage_type=path",
                "--example_output_format=PYTEST",
                str(target_file_info.module_name),
            ])
            options = DEFAULT_OPTIONS.overlay(AnalysisOptionSet(
                #max_uninteresting_iterations=50,
                max_iterations=300,
                per_path_timeout=2.0,
                per_condition_timeout=240.0
            ))
            set_debug(False)
            sys.path.append(str(target_file_info.config.targets_dir))
            start = time.time()
            retcode = cover(args, options, stdout, stderr)
            cur_time = time.time() - start
            GENERATION_TIMES.append(cur_time)
            print("Process finished in", cur_time)
            print("Mean time:", sum(GENERATION_TIMES) / len(GENERATION_TIMES))
            print("Max time:", max(GENERATION_TIMES))

        except exc:
            traceback.print_exc()
            return TestGenerationFailure((exc,), FailureReason.UNEXPECTED_ERROR)
        if retcode == 0:
            test_body = stdout.getvalue()
            if test_body:
                #print("Generated!")
                #print(test_body)
                return TestGenerationSuccess(test_body)
            else:
                return TestGenerationFailure(("CrossHair did not generate any tests",), FailureReason.NOTHING_GENERATED)
        else:
            error_str = stderr.getvalue()
            return TestGenerationFailure(
                    (error_str,), FailureReason.UNEXPECTED_ERROR
                )
