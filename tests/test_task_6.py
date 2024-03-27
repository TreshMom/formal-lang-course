from tempfile import NamedTemporaryFile
from project.task6 import cfg_from_file, cfg_to_wnf
from textwrap import dedent


def test_cfg_from_file_to_wnf():
    with NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(
            dedent(
                """\
                S -> [ S ] S
                S -> epsilon
                """
            )
        )
        path = f.name

    expected_lines = """\
        S ->
        [#CNF# -> [
        S -> "VAR:[#CNF#" C#CNF#1
        C#CNF#2 -> "VAR:]#CNF#" S
        C#CNF#1 -> S C#CNF#2
        ]#CNF# -> ]
    """.strip().split(
        "\n"
    )
    expected = {line.strip() for line in expected_lines}
    wnf = cfg_to_wnf(cfg_from_file(path))
    got_lines = wnf.to_text().strip().split("\n")
    got = {line.strip() for line in got_lines}
    assert expected == got
