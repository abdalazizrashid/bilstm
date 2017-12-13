"""Full Bi-LSTM network."""
# pylint: disable=W0221
# pylint: disable=E1101
import torch
import torch.nn as nn
import torch.autograd as autograd
from torch.nn.utils.rnn import pack_padded_sequence
import torchvision.models as models


class FullBiLSTM(nn.Module):
    """Bi-LSTM architecture definition.

    Args:
        - input_dim: dimension of the input.
        - hidden_dim: dimension of the hidden/output layer.
        - [batch_first]: parameter of the PackedSequence data.
        - [dropout]: dropout value for LSTM.

    """

    def __init__(self, input_dim, hidden_dim, batch_first=False, dropout=0):
        """Create the network."""
        super(FullBiLSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.batch_first = batch_first
        self.cnn = models.inception_v3(pretrained=True)
        self.cnn.fc = nn.Linear(2048, input_dim)
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=1,
                            batch_first=self.batch_first, bidirectional=True,
                            dropout=dropout)

    def forward(self, images, seq_lens, lookup_table, hidden):
        """Do a forward pass.

        The forward pass implies:
            - A normal forward of the images through a CNN.
            - A pass of the texts through a text embedding.
            - Transforming the image features to a pytorch PackedSequence.
            - Doing the forward pass through the LSTM.

        Args:
            - images: autograd Variable with the images of the batch.
            - seq_lens: torch tensor with a list of the sequence lengths.
            - lookup_table: list of lists with indices of the images.
            - hidden: hidden variables for the LSTM.

        Returns:
            - features extracted from the CNN (PackedSequence)
            - (out, hidden): outputs and hidden states of the LSTM.

        """
        # Then, get their features:
        feats, _ = self.cnn(images)
        # Pack the sequences:
        packed_feats = self.create_packed_seq(feats, seq_lens, lookup_table)
        # Forward the sequence through the LSTM:
        return packed_feats, self.lstm(packed_feats, hidden)

    def init_hidden(self, batch_size):
        """Initialize the hidden state and cell state."""
        return (autograd.Variable(torch.randn(2, batch_size, self.hidden_dim)),
                autograd.Variable(torch.randn(2, batch_size, self.hidden_dim)))

    def create_packed_seq(self, feats, seq_lens, lookup_table):
        """Create a packed input of sequences for a RNN.

        Args:
            - feats: torch.Tensor with data features (N imgs x feat_dim).
            - seq_lens: sequence lengths.
            - lookup_table: list of image indices from seqs2batch.
            - data: list (with length batch_size) of sequences of images (shaped seq_len x img_dim).

        Returns:
            - torch PackedSequence (batch_size x max_seq_len x img_dim if batch_first = True,
                                    max_seq_len x batch_size x img_dim otherwise).

        """
        # Manually create the padded sequence.
        if feats.is_cuda:
            seqs = autograd.Variable(torch.zeros((len(seq_lens), max(seq_lens),
                                                  feats.size()[1]))).cuda()
        else:
            seqs = autograd.Variable(torch.zeros((len(seq_lens), max(seq_lens), feats.size()[1])))

        for i, seq_len in enumerate(seq_lens):  # Iterate over batch
            for j in range(max(seq_lens)):  # Iterate over sequence
                if j < seq_len:
                    seqs[i, j] = feats[lookup_table[i][j]]
                else:
                    seqs[i, j] = autograd.Variable(torch.zeros(feats.size()[1]))

        # In order to be packed, sequences must be ordered from larger to shorter.
        seqs = seqs[sorted(range(len(seq_lens)), key=lambda k: seq_lens[k], reverse=True), :]
        ordered_seq_lens = sorted(seq_lens, reverse=True)

        # seqs is (batch size, max length, data_dim)
        if not self.batch_first:
            seqs = seqs.permute(1, 0, 2)  # now it is (max length, max length, data_dim)

        return pack_padded_sequence(seqs, ordered_seq_lens, batch_first=self.batch_first)