"""Unit tests for //lib/labm8:fmt."""
import pytest
import sys
from absl import app
from phd.lib.labm8 import fmt


def test_IndentList_zero():
  """Indent with 0 spaces is equivalent to the input strings."""
  assert fmt.IndentList(0, ['abc', 'd']) == ['abc', 'd']


def test_IndentList_two():
  """Test indent with two spaces."""
  assert fmt.IndentList(2, ['abc', 'd']) == ['  abc', '  d']


def test_Indent_zero():
  """Indent with 0 spaces is equivalent to the input string."""
  assert fmt.Indent(0, 'abc\nd') == 'abc\nd'


def test_Indent_two():
  """Test indent with two spaces."""
  assert fmt.Indent(2, 'abc\nd') == '  abc\n  d'


def test_table():
  assert (["foo", "1", "bar", "2"] ==
          fmt.table((("foo", 1), ("bar", 2))).split())


def test_table_columns():
  assert ((["type", "value", "foo", "1", "bar", "2"]) ==
          fmt.table((("foo", 1), ("bar", 2)),
                    columns=("type", "value")).split())


def test_table_bad_columns():
  with pytest.raises(fmt.Error):
    fmt.table((("foo", 1), ("bar", 2)),
              columns=("type", "value", "too", "many", "values"))


def test_table_bad_rows():
  with pytest.raises(fmt.Error):
    fmt.table((("foo", 1), ("bar", 2), ("car",)))


def main(argv):  # pylint: disable=missing-docstring
  del argv
  sys.exit(pytest.main([__file__, '-v']))


if __name__ == '__main__':
  app.run(main)
