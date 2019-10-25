import torch
import joblib
import torch.nn as nn
from torch.optim import Adam
# from torch.utils import data

import utils
import config
# from Dataset import Dataset
from Encoder import EncoderRNN
from Decoder import DecoderRNN


def train_model(encoder, decoder, criterion, encoder_optimizer, decoder_optimizer, input_elems, output_elems, num_epochs=3):
    for epoch in range(num_epochs):
        print("Current epoch: {}".format(epoch + 1))
        epoch_loss = 0.0
        # for input_tensors, input_lengths, output_tensors in training_generator:
        for index in range(0, len(input_elems[1]), config.batch_size):
            input_tensors = input_elems[0][:, index: index + config.batch_size]
            input_lengths = input_elems[1][index: index + config.batch_size]
            output_tensors = output_elems[0][:, index: index + config.batch_size]
            max_seq_length = output_elems[2]

            if input_tensors.shape[1] < config.batch_size:
                continue
            # set gradients of optimizers to 0
            encoder_optimizer.zero_grad()
            decoder_optimizer.zero_grad()

            # input_tensors, input_lengths = input_elems
            # output_tensors, _, max_seq_length = output_elems

            # forward pass for encoder
            encoder_output, encoder_hidden = encoder(input_tensors, input_lengths)

            # the starting input for the decoder will always be start_token, for all inputs in the batch
            decoder_input = torch.LongTensor([[vocabulary.START_TOKEN for _ in range(output_tensors.shape[1])]])
            decoder_hidden = encoder_hidden[:config.decoder_num_layers]
            loss = 0.0
            for i in range(max_seq_length):
                decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden, encoder_output)
                # using teacher forcing here
                decoder_input = torch.stack([output_tensors[i, :]])

                target = output_tensors[i]
                mask_loss = criterion(decoder_output, target)
                loss += mask_loss
            # print("\tLoss: {}".format(loss.item()))
            epoch_loss += loss.item()
            loss.backward()
            # may need to do gradient clipping here
            encoder_optimizer.step()
            decoder_optimizer.step()
        print("Epoch loss: {}".format(epoch_loss))
    return encoder, decoder


if __name__ == '__main__':
    dataset = joblib.load(config.mapped_sequences)
    vocabulary, sent_pairs = utils.prepare_training_data(dataset[:1000])
    input_elems, output_elems = utils.generate_training_data(sent_pairs, vocabulary)

    # input_tensors, input_lengths = input_elems
    # output_tensors, binary_mask, max_seq_length = output_elems

    # create training_generator here
    # params = {
    #     'batch_size': config.batch_size,
    #     'shuffle': True
    # }
    # training_set = Dataset(input_tensors, input_lengths, output_tensors)
    # training_generator = data.DataLoader(training_set, **params)

    # initialize embedding -> this will be used in both encoder and decoder
    embedding = nn.Embedding(vocabulary.num_words, config.encoder_hidden_size)

    # initialize the encoder and decoder
    encoder = EncoderRNN(embedding, hidden_size=config.encoder_hidden_size)
    decoder = DecoderRNN(embedding, hidden_size=config.decoder_hidden_size,
                         output_size=vocabulary.num_words, num_layers=config.decoder_num_layers)
    criterion = nn.NLLLoss(ignore_index=vocabulary.PAD_TOKEN)
    encoder_optimizer = Adam(encoder.parameters(), lr=config.encoder_lr)
    decoder_optimizer = Adam(decoder.parameters(), lr=config.decoder_lr)

    # train_model(encoder, decoder, criterion, encoder_optimizer, decoder_optimizer, training_generator, max_seq_length)
    train_model(encoder, decoder, criterion, encoder_optimizer, decoder_optimizer, input_elems, output_elems, num_epochs=20)
