from __future__ import unicode_literals, print_function, division

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from io import open
import unicodedata
import operator
import string
import re
import random
import numpy as np

import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
from gensim.models import FastText
MAX_LENGTH = 20
hidden_size = 256

fastText = FastText.load(BASE_DIR + '/../models/FastText.model')
words= []
word2index = {}
idx = 0
for word in fastText.wv.vocab.keys():
  words.append(word)
  word2index[word] = idx
  idx += 1

sos_index = word2index['SOS']
eos_index = word2index['EOS']
sos_swap_word = words[0]
eos_swap_word = words[1]
 
words[0], words[sos_index] = words[sos_index], words[0]
words[1], words[eos_index] = words[eos_index], words[1]
word2index[sos_swap_word], word2index['SOS'] = word2index['SOS'], word2index[sos_swap_word]
word2index[eos_swap_word], word2index['EOS'] = word2index['EOS'], word2index[eos_swap_word]
word2index = { k : v for k , v in sorted(word2index.items(), key=operator.itemgetter(1))}

# vocab dictionary

SOS = 0
EOS = 1

class Lang:
  def __init__(self, name):
    self.name = name
    self.word2index = { k : v for k , v in sorted(word2index.items(), key=operator.itemgetter(1))}
    self.word2count = { word : 1 for word in words }
    self.index2word = { i : word for word, i in word2index.items() }
    self.n_words =  7271
  
  def addSentence(self, sentence):
    for word in sentence.split(' '):
      self.addWord(word)
  
  def addWord(self, word):
    if word not in self.word2index:
      self.word2index[word] = self.n_words
      self.word2count[word] = 1
      self.index2word[self.n_words] = word
      self.n_words += 1
    else:
      self.word2count[word] += 1
lang = Lang("")

matrix_len = lang.n_words
 
weights_matrix = np.zeros((matrix_len, 256))
words_found = 0
 
for i, word in enumerate(lang.word2index):
    try: 
        weights_matrix[i] = fastText.wv[word]
        words_found += 1
    except KeyError:
        weights_matrix[i] = np.random.normal(scale=0.6, size=(4, ))

class EncoderRNN(nn.Module):
  def __init__(self, input_size, hidden_size):
    super(EncoderRNN, self).__init__()    
    self.hidden_size = hidden_size

    self.embedding = nn.Embedding(input_size, hidden_size)
    self.embedding.weight.data.copy_(torch.from_numpy(weights_matrix))
    #self.embedding = nn.Embedding.from_pretrained(fastModel.wv.vectors, freeze=False)
    self.gru = nn.GRU(hidden_size, hidden_size)

  def forward(self, input, hidden):
    embedded = self.embedding(input).view(1, 1, -1)
    output = embedded
    output, hidden = self.gru(output, hidden)
    return output, hidden

  def initHidden(self):
    #return torch.zeros(1, 1, self.hidden_size, device=device)
    return torch.zeros(1, 1, self.hidden_size)

class AttnDecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout_p = dropout_p
        self.max_length = max_length

        self.embedding = nn.Embedding(self.output_size, self.hidden_size)
        self.embedding.weight.data.copy_(torch.from_numpy(weights_matrix))
        #self.embedding = nn.Embedding.from_pretrained(fastModel.wv.vectors, freeze=False)
        self.attn = nn.Linear(self.hidden_size * 2, self.max_length)
        self.attn_combine = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.dropout = nn.Dropout(self.dropout_p)
        self.gru = nn.GRU(self.hidden_size, self.hidden_size)
        self.out = nn.Linear(self.hidden_size, self.output_size)

    def forward(self, input, hidden, encoder_outputs):
        embedded = self.embedding(input).view(1, 1, -1)
        embedded = self.dropout(embedded)

        attn_weights = F.softmax(
            self.attn(torch.cat((embedded[0], hidden[0]), 1)), dim=1)
        attn_applied = torch.bmm(attn_weights.unsqueeze(0),
                                 encoder_outputs.unsqueeze(0))

        output = torch.cat((embedded[0], attn_applied[0]), 1)
        output = self.attn_combine(output).unsqueeze(0)

        output = F.relu(output)
        output, hidden = self.gru(output, hidden)

        output = F.log_softmax(self.out(output[0]), dim=1)
        return output, hidden, attn_weights

    def initHidden(self):
        #return torch.zeros(1, 1, self.hidden_size, device=device)
        return torch.zeros(1, 1, self.hidden_size)

encoder = EncoderRNN(lang.n_words, hidden_size)
decoder = AttnDecoderRNN(hidden_size, lang.n_words, dropout_p=0.1)

encoder.load_state_dict(torch.load(BASE_DIR + '/../models/encoder.dict'))
decoder.load_state_dict(torch.load(BASE_DIR + '/../models/decoder.dict'))

def indexesFromSentence(lang, sentence):
  # sentence == ['늘:VV 었:EP 네요:SEF past exclamation', '늘:VV 었:EP 구나:SEF']
  wordList = sentence.strip().split(' ')  
  try:
    for word in wordList:
        if word == '':
          wordList.remove(word)
  except:
    print(wordList)
  return [lang.word2index[word] for word in wordList]
   


def tensorFromSentence(sentence):
    indexes = indexesFromSentence(lang, sentence)
    indexes.append(EOS)
    #return torch.tensor(indexes, dtype=torch.long, device=device).view(-1, 1)
    return torch.tensor(indexes, dtype=torch.long).view(-1, 1)


def tensorsFromPair(pair):
    #print(pair)
    input_tensor = tensorFromSentence(pair[0])
    target_tensor = tensorFromSentence(pair[1])
    return (input_tensor, target_tensor)

def OOVChecker(sentence):
  flag = False
  sentence = sentence.split()
  for word in sentence:
    if word == '':
      sentence.remove(word)
  for i in range(0, len(sentence)):
    if sentence[i] not in fastText.wv.vocab:
      oovVec = fastText.wv[sentence[i]]
      (sentence[i], prob) = fastText.wv.most_similar(positive=[sentence[i]])[0]
      flag = True
      break
  return ' '.join(sentence), flag

def evaluate(sentence, max_length=MAX_LENGTH):
    with torch.no_grad():
        originalVerb = sentence.split()[0]
        sentence, flag = OOVChecker(sentence)
        input_tensor = tensorFromSentence(sentence)
        # input_tensor = tensorFromSentence(lang, sentence)
        input_length = input_tensor.size()[0]
        encoder_hidden = encoder.initHidden()

        #encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)
        encoder_outputs = torch.zeros(max_length, encoder.hidden_size)

        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei],
                                                     encoder_hidden)
            encoder_outputs[ei] += encoder_output[0, 0]

        #decoder_input = torch.tensor([[SOS]], device=device)  # SOS
        decoder_input = torch.tensor([[SOS]])  # SOS

        decoder_hidden = encoder_hidden

        decoded_words = []
        decoder_attentions = torch.zeros(max_length, max_length)

        for di in range(max_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            decoder_attentions[di] = decoder_attention.data
            topv, topi = decoder_output.data.topk(1)
            
            if topi.item() == EOS:
                decoded_words.append('<EOS>')
                break
            elif di == 0:
                decoded_words.append(lang.index2word[input_tensor[0].item()])
            else:
                decoded_words.append(lang.index2word[topi.item()])

            
            decoder_input = topi.squeeze().detach()

        if flag:
          decoded_words[0] = originalVerb

        return decoded_words

# test
# print(evaluate('좋:VA 거든:SEF future polite'))
