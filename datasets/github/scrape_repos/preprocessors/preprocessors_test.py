"""Unit tests for //datasets/github/scrape_repos/preprocessors.py."""
import pathlib
import sys
import tempfile

import pytest
from absl import app
from absl import logging

from datasets.github.scrape_repos.preprocessors import preprocessors
from datasets.github.scrape_repos.preprocessors import public


@pytest.fixture(scope='function')
def tempdir() -> pathlib.Path:
  """Test fixture for an empty temporary directory."""
  with tempfile.TemporaryDirectory() as d:
    yield pathlib.Path(d)


def MakeFile(directory: pathlib.Path, relpath: str, contents: str):
  """Write contents to a file."""
  abspath = (directory / relpath).absolute()
  abspath.parent.mkdir(parents=True, exist_ok=True)
  with open(abspath, 'w') as f:
    f.write(contents)


@public.dataset_preprocessor
def MockPreprocessor(import_root: pathlib.Path, file_relpath: str,
                     text: str) -> str:
  """A mock preprocessor."""
  del import_root
  del file_relpath
  return 'PREPROCESSED'


@public.dataset_preprocessor
def MockPreprocessorError(import_root: pathlib.Path, file_relpath: str,
                          text: str) -> str:
  """A mock preprocessor which raises a ValueError."""
  del import_root
  del file_relpath
  raise ValueError('ERROR')


def MockUndecoratedPreprocessor(import_root: pathlib.Path,
                                file_relpath: str, text: str) -> str:
  """A mock preprocessor which is not decorated with @dataset_preprocessor."""
  del import_root
  del file_relpath
  return 'UNDECORATED'


# GetPreprocessFunction() tests.

def test_GetPreprocessFunction_empty_string():
  """Test that a ValueError is raised if no preprocessor is given."""
  with pytest.raises(ValueError) as e_info:
    preprocessors.GetPreprocessorFunction('')
  assert 'Invalid preprocessor name' in str(e_info.value)


def test_GetPreprocessFunction_missing_module():
  """Test that ValueError is raised if module not found."""
  with pytest.raises(ValueError) as e_info:
    preprocessors.GetPreprocessorFunction('not.a.real.module:Foo')
  assert 'not found' in str(e_info.value)


def test_GetPreprocessFunction_missing_function():
  """Test that ValueError is raised if module exists but function doesn't."""
  with pytest.raises(ValueError) as e_info:
    preprocessors.GetPreprocessorFunction(
        'datasets.github.scrape_repos.preprocessors.preprocessors_test:Foo')
  assert 'not found' in str(e_info.value)


def test_GetPreprocessFunction_undecorated_preprocessor():
  """Test that an ValueError is raised if preprocessor not decorated."""
  with pytest.raises(ValueError) as e_info:
    preprocessors.GetPreprocessorFunction(
        'datasets.github.scrape_repos.preprocessors.preprocessors_test'
        ':MockUndecoratedPreprocessor')
  assert '@dataset_preprocessor' in str(e_info.value)


def test_GetPreprocessFunction_mock_preprocessor():
  """Test that a mock preprocessor can be found."""
  f = preprocessors.GetPreprocessorFunction(
      'datasets.github.scrape_repos.preprocessors.preprocessors_test:MockPreprocessor')
  assert f == MockPreprocessor


# Preprocess() tests.


def test_Preprocess_no_preprocessors(tempdir):
  """Test unmodified output if no preprocessors."""
  MakeFile(tempdir, 'a', 'hello')
  assert preprocessors.Preprocess(tempdir, 'a', []) == 'hello'


@pytest.mark.skip(reason='TODO(cec):')
def test_Preprocess_mock_preprocessor(tempdir):
  """Test unmodified output if no preprocessors."""
  assert preprocessors.Preprocess('hello', [
    'datasets.github.scrape_repos.preprocessors.preprocessors_test:MockPreprocessor']) \
         == 'PREPROCESSED'


@pytest.mark.skip(reason='TODO(cec):')
def test_Preprocess_mock_preprocessor_exception(tempdir):
  """Test that an exception is propagated."""
  with pytest.raises(ValueError):
    preprocessors.Preprocess('', [
      'datasets.github.scrape_repos.preprocessors.preprocessors_test'
      ':MockPreprocessorInternalError'])


# Benchmarks.

def test_benchmark_GetPreprocessFunction_mock(benchmark):
  """Benchmark GetPreprocessFunction."""
  benchmark(preprocessors.GetPreprocessorFunction,
            'datasets.github.scrape_repos.preprocessors.preprocessors_test'
            ':MockPreprocessor')


def main(argv):
  """Main entry point."""
  if len(argv) > 1:
    raise app.UsageError('Unrecognized command line flags.')
  logging.set_verbosity(logging.DEBUG)
  sys.exit(pytest.main([__file__, '-vv']))


if __name__ == '__main__':
  app.run(main)