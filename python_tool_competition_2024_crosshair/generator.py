"""A test generator using CrossHair."""
import python_tool_competition_2024_crosshair.codegen_substitute

from io import StringIO
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
        try:
            stdout, stderr = StringIO(), StringIO()
            args = command_line_parser().parse_args([
                "cover",
                "--coverage_type=path",
                "--example_output_format=PYTEST",
                "--max_uninteresting_iterations=180",
                "--per_path_timeout=1",
                str(target_file_info.absolute_path),
            ])
            options = DEFAULT_OPTIONS.overlay(AnalysisOptionSet(
                per_condition_timeout=60,
                max_uninteresting_iterations=50,
            ))
            retcode = cover(args, options, stdout, stderr)
        except Exception as exc:
            traceback.print_exc()
            return TestGenerationFailure((exc,), FailureReason.UNEXPECTED_ERROR)
        if retcode == 0:
            test_body = stdout.getvalue()
            if test_body:
                return TestGenerationSuccess(test_body)
            else:
                return TestGenerationFailure(("CrossHair did not generate any tests",), FailureReason.NOTHING_GENERATED)
        else:
            error_str = stderr.getvalue()
            return TestGenerationFailure(
                    (error_str,), FailureReason.UNEXPECTED_ERROR
                )
