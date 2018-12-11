# Copyright 2018, The TensorFlow Federated Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for compiler_pipeline.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports
from absl.testing import absltest
import tensorflow as tf

from tensorflow_federated.python.core.api import computations
from tensorflow_federated.python.core.api import intrinsics
from tensorflow_federated.python.core.api import placements
from tensorflow_federated.python.core.api import types

from tensorflow_federated.python.core.impl import compiler_pipeline
from tensorflow_federated.python.core.impl import computation_building_blocks
from tensorflow_federated.python.core.impl import computation_impl
from tensorflow_federated.python.core.impl import intrinsic_defs
from tensorflow_federated.python.core.impl import transformations


class CompilerPipelineTest(absltest.TestCase):

  def test_compile_computation(self):
    @computations.federated_computation([
        types.FederatedType(tf.float32, placements.CLIENTS),
        types.FederatedType(tf.float32, placements.SERVER, True)])
    def foo(temperatures, threshold):
      return intrinsics.federated_sum(intrinsics.federated_map(
          [temperatures, intrinsics.federated_broadcast(threshold)],
          computations.tf_computation(
              lambda x, y: tf.to_int32(tf.greater(x, y)),
              [tf.float32, tf.float32])))
    foo_proto = computation_impl.ComputationImpl.get_proto(foo)
    transformed_foo = (
        computation_building_blocks.ComputationBuildingBlock.from_proto(
            compiler_pipeline.compile_computation(foo_proto)))

    def _not_federated_sum(x):
      if isinstance(x, computation_building_blocks.Intrinsic):
        self.assertNotEqual(x.uri, intrinsic_defs.FEDERATED_SUM.uri)
      return x

    transformations.transform_postorder(transformed_foo, _not_federated_sum)

    # TODO(b/113123410): Expand the test with more structural invariants.


if __name__ == '__main__':
  absltest.main()