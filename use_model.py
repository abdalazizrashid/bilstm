"""Script for using the model in model.py with sequence inputs."""
import torch
import torch.nn as nn
import torch.autograd as autograd
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


def create_random_packed_seq(data_dim, seq_lens):
    """Create a packed input of sequences for a RNN."""
    seqs = [autograd.Variable(torch.randn(data_dim, sl)) for sl in seq_lens]
    t_seqs = []
    for seq in seqs:
        if seq.size()[1] < max(seq_lens):
            t_seqs.append(torch.cat((seq, torch.zeros(data_dim, max(seq_lens) - seq.size()[1])), 1))
        else:
            t_seqs.append(seq)

    t_seqs = torch.stack(t_seqs)  # t_seqs is (batch size, data_dim, max length)
    t_seqs = t_seqs.permute(0, 2, 1)  # now it is (batch size, max length, data_dim)

    return pack_padded_sequence(t_seqs, seq_lens, batch_first=True)


class Network(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        """Create the network."""
        super(Network, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.lstm = nn.LSTM(input_dim, hidden_dim)

    def forward(self, data, hidden):
        """Do a forward pass."""
        return self.lstm(data, hidden)

    def init_hidden(self):
        return (autograd.Variable(torch.randn(1, 1, self.hidden_dim)),
                autograd.Variable(torch.randn(1, 1, self.hidden_dim)))


def main():
    """Forward sequences."""
    seq_lens = [5, 5, 3, 1]  # batch size = 4, max length = 5
    input_dim = 100
    hidden_dim = 150
    data = create_random_packed_seq(input_dim, seq_lens)

    model = Network(input_dim, hidden_dim)
    hidden = model.init_hidden()
    out, hidden = model.forward(data, hidden)
    out, _ = pad_packed_sequence(out, batch_first=True)  # 2nd output are the sequence lengths


if __name__ == '__main__':
    main()
