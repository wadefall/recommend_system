import tensorflow as tf
tf.random.set_seed(7)
from tensorflow.keras.layers import Input, Dense, Embedding
from tensorflow.keras.models import Model


class FM(tf.keras.Model):
    def __init__(self,
                 input_len=2,
                 input_dim=10,
                 embedding_dim=8):
        super(FM, self).__init__()

        self.input_len = input_len
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim

        # one-order weights, bias_weight_index = input_dim
        self.one_order_embedding_layer = Embedding(input_dim=input_dim+1, output_dim=1)

        # two-orders weights
        self.two_order_embedding_layer = Embedding(input_dim=input_dim, output_dim=embedding_dim)

    def _compute_fm_1d(self,
                       bias_indexes=None,
                       one_order_embedding=None,
                       input_values=None):
        # bias_indexes: [None, 1]
        # one_order_embedding: [None, input_len, 1]
        # input_values: [None, input_len]
        # Return: [None, 1]

        # === bias, [None, 1, 1] <= [None, 1]
        bias = self.one_order_embedding_layer(bias_indexes)

        # [None, 1]
        bias = tf.squeeze(bias, axis=-1)

        # === 1d
        # [None, input_len]
        one_order_outputs = tf.multiply(input_values, tf.squeeze(one_order_embedding, -1))

        # [None, 1]
        one_order_outputs = tf.reduce_sum(one_order_outputs, axis=1, keepdims=True)

        # === bias + fm_1d
        # [None, 1]
        fm_1d = one_order_outputs + bias

        return fm_1d

    def _compute_fm_2d(self, two_order_embedding=None,
                       input_values=None):
        # two_order_embedding: [None, input_len, embedding_dim]
        # input_values: [None, input_len]
        # Return: [None, 1]

        # embedding_value = embedding * value, V_{f, i} * x_i
        #   [None, input_len, embedding_dim], use broadcast of tf.
        embedding_value = tf.multiply(two_order_embedding,
                                    tf.expand_dims(input_values, axis=-1))

        # (\sum_i v_{f, i} * x_i) ^ 2,  f: embedding_dim, i: input_len
        # [None, embedding_dim]
        square_of_sum = tf.square(tf.reduce_sum(embedding_value, axis=1))

        # \sum_i ((v_{f, i} * x_i) ^ 2)
        # [None, embedding_dim]
        sum_of_square = tf.reduce_sum(tf.square(embedding_value), axis=1)

        # \sum_f
        # [None, 1]
        fm_2d = 0.5 * tf.reduce_sum(square_of_sum - sum_of_square, axis=-1, keepdims=True)

        return fm_2d

    def call(self, inputs, training=None, mask=None):
        # y = (bias + one-order) + two-order
        # y = w_0 + \sum_i w_i x_i +
        #   1/2 * \sum_f ((\sum_i v_{f_i} * x_i)^2 - \sum_i v_{f, i}^2 * x_i^2)

        # input_values: [None, seq_len]
        input_values, input_indexes, bias_indexes = inputs

        # === Embedding
        # [None, input_len, 1] <= [None, input_len]
        one_order_embedding = self.one_order_embedding_layer(input_indexes)

        # [None, input_len, embedding_dim]
        two_order_embedding = self.two_order_embedding_layer(input_indexes)

        # === one_order, [None, 1]
        y_fm_1d = self._compute_fm_1d(bias_indexes=bias_indexes,
                                    one_order_embedding=one_order_embedding,
                                    input_values=input_values)

        # === two_order, [None, 1]
        y_fm_2d = self._compute_fm_2d(two_order_embedding=two_order_embedding,
                                    input_values=input_values)

        # [None, 1]
        outputs = y_fm_1d + y_fm_2d

        return outputs


def test_model_once(model=None, input_len=None, input_dim=None):
    batch_size = 2

    input_values = tf.random.uniform((batch_size, input_len))
    input_indexes = tf.random.uniform((batch_size, input_len), minval=0, maxval=input_dim, dtype=tf.int32)
    bias_indexes = tf.constant([[input_dim-1]] * batch_size, dtype=tf.int32)

    # num_user = 6, num_item = 4
    # user: 0~5, item: 6~9
    #input_values = tf.constant(([[1, 1]]), dtype=tf.float32)
    #input_indexes = tf.constant([[4, 7]], dtype=tf.int32)
    #bias_indexes = tf.constant([[10]], dtype=tf.int32)

    inputs = (input_values, input_indexes, bias_indexes)
    outputs = model(inputs)
    return outputs


if __name__ == '__main__':
    num_user = 6
    num_item = 4

    input_len = 2
    input_dim = num_user + num_item
    embedding_dim = 8

    model = FM(input_len=input_len, input_dim=input_dim, embedding_dim=embedding_dim)
    #model.build(input_shape=(None, 448, 448, 3))
    #print(model.summary())
    outputs = test_model_once(model=model, input_len=input_len, input_dim=input_dim)
    print(outputs.shape)
