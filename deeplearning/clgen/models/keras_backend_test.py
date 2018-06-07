"""Unit tests for //deeplearning/clgen/models/keras_backend.py."""
import checksumdir
import numpy as np
import pytest
import sys
from absl import app

from deeplearning.clgen.models import keras_backend
from deeplearning.clgen.proto import model_pb2
from deeplearning.clgen.proto import telemetry_pb2
from lib.labm8 import crypto
from lib.labm8 import pbutil


class MockSampler(object):
  """Mock class for a Sampler."""

  # The default value for start_text has been chosen to only use characters and
  # words from the abc_corpus, so that it may be encoded using the vocabulary
  # of that corpus.
  def __init__(self, start_text: str = 'H', hash: str = 'hash',
               batch_size: int = 1):
    self.start_text = start_text
    self.encoded_start_text = np.array([1, 2, 3])
    self.tokenized_start_text = ['a', 'b', 'c']
    self.temperature = 1.0
    self.hash = hash
    self.batch_size = batch_size

  @staticmethod
  def Specialize(atomizer):
    """Atomizer.Specialize() mock."""
    pass

  @staticmethod
  def SampleIsComplete(sample_in_progress):
    """Crude 'maxlen' mock."""
    return len(sample_in_progress) >= 10


# KerasEmbeddingModel tests.

def test_KerasEmbeddingModel_directories(clgen_cache_dir, abc_model_config):
  """A newly instantiated model's cache has checkpoint and sample dirs."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert (m.cache.path / 'embeddings').is_dir()
  assert not list((m.cache.path / 'embeddings').iterdir())


def test_KerasEmbeddingModel_epoch_checkpoints_untrained(clgen_cache_dir,
                                                         abc_model_config):
  """Test that an untrained model has no checkpoint files."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert not m.epoch_checkpoints


def test_KerasEmbeddingModel_is_trained(clgen_cache_dir, abc_model_config):
  """Test that is_trained changes to True when model is trained."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert not m.is_trained
  m.Train()
  assert m.is_trained


def test_KerasEmbeddingModel_is_trained_new_instance(clgen_cache_dir,
                                                     abc_model_config):
  """Test that is_trained is True on a new instance of a trained model."""
  del clgen_cache_dir
  m1 = keras_backend.KerasEmbeddingModel(abc_model_config)
  m1.Train()
  m2 = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert m2.is_trained


# KerasEmbeddingModel.Train() tests.

def test_KerasEmbeddingModel_Train_epoch_checkpoints(clgen_cache_dir,
                                                     abc_model_config):
  """Test that a trained model generates weight checkpoints."""
  del clgen_cache_dir
  abc_model_config.training.num_epochs = 2
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  m.Train()
  assert len(m.epoch_checkpoints) == 2
  for path in m.epoch_checkpoints:
    assert path.is_file()


def test_KerasEmbeddingModel_Train_telemetry(clgen_cache_dir, abc_model_config):
  """Test that model training produced telemetry files."""
  del clgen_cache_dir
  abc_model_config.training.num_epochs = 2
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert len(m.TrainingTelemetry()) == 0
  m.Train()
  assert len(m.TrainingTelemetry()) == 2
  for telemetry in m.TrainingTelemetry():
    assert isinstance(telemetry, telemetry_pb2.ModelEpochTelemetry)


def test_KerasEmbeddingModel_Train_twice(clgen_cache_dir, abc_model_config):
  """Test that TensorFlow checkpoint does not change after training twice."""
  del clgen_cache_dir
  abc_model_config.training.num_epochs = 1
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  m.Train()
  f1a = checksumdir.dirhash(m.cache.path / 'checkpoints')
  f1b = crypto.md5_file(m.cache.path / 'META.pbtxt')
  m.Train()
  f2a = checksumdir.dirhash(m.cache.path / 'checkpoints')
  f2b = crypto.md5_file(m.cache.path / 'META.pbtxt')
  assert f1a == f2a
  assert f1b == f2b


# TODO(cec): Add tests on incrementally trained model predictions and losses.


# KerasEmbeddingModel.Sample() tests.

def test_KerasEmbeddingModel_Sample_implicit_train(clgen_cache_dir,
                                                   abc_model_config):
  """Test that Sample() implicitly trains the model."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert not m.is_trained
  m.Sample(MockSampler(), 1)
  assert m.is_trained


def test_KerasEmbeddingModel_Sample_return_value_matches_cached_sample(
    clgen_cache_dir,
    abc_model_config):
  """Test that Sample() returns Sample protos."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  samples = m.Sample(MockSampler(hash='hash'), 1)
  assert len(samples) == 1
  assert len(list((m.cache.path / 'samples' / 'hash').iterdir())) == 1
  cached_sample_path = (m.cache.path / 'samples' / 'hash' /
                        list((m.cache.path / 'samples' / 'hash').iterdir())[0])
  assert cached_sample_path.is_file()
  cached_sample = pbutil.FromFile(cached_sample_path, model_pb2.Sample())
  assert samples[0].text == cached_sample.text
  assert samples[0].sample_time_ms == cached_sample.sample_time_ms
  assert samples[
           0].sample_start_epoch_ms_utc == cached_sample.sample_start_epoch_ms_utc


def test_KerasEmbeddingModel_Sample_exact_multiple_of_batch_size(
    clgen_cache_dir,
    abc_model_config):
  """Test that min_num_samples are returned when a multiple of batch_size."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  assert len(m.Sample(MockSampler(batch_size=2), 2)) == 2
  assert len(m.Sample(MockSampler(batch_size=2), 4)) == 4


def test_KerasEmbeddingModel_GetInferenceModel_predict_output_shape(
    clgen_cache_dir,
    abc_model_config):
  """Test that predict() on inference model is one-hot encoded."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  im, batch_size = m.GetInferenceModel()
  probabilities = im.predict(np.array([[0]]) * batch_size)
  assert (batch_size, 1, m.corpus.vocab_size) == probabilities.shape


# WeightedPick() tests.

def test_WeightedPick_output_range():
  """Test that WeightedPick() returns an integer index into array"""
  a = [1, 2, 3, 4]
  assert 0 <= keras_backend.WeightedPick(np.array(a), 1.0) <= len(a)


# Benchmarks.

def test_benchmark_KerasEmbeddingModel_Train_already_trained(
    clgen_cache_dir, abc_model_config, benchmark):
  """Benchmark the Train() method on an already-trained model."""
  del clgen_cache_dir
  m = keras_backend.KerasEmbeddingModel(abc_model_config)
  m.Train()  # "Offline" training from cold.
  benchmark(m.Train)


def main(argv):
  """Main entry point."""
  if len(argv) > 1:
    raise app.UsageError('Unrecognized command line flags.')
  sys.exit(pytest.main([__file__, '-v']))


if __name__ == '__main__':
  app.run(main)