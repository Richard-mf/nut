# Author: Peter Prettenhofer <peter.prettenhofer@gmail.com>
#
# License: BSD Style.
"""
tagger
======

TODO docs
"""

import numpy as np
import bolt

from collections import defaultdict
from itertools import chain
from ..util import timeit
from ..ner.nonlocal import ExtendedPredictionHistory


@timeit
def build_vocabulary(reader, fd, hd, minc=1, use_eph=False):
    """
    Arguments
    ---------

    Returns
    -------
    vocabulary : list
        A sorted list of feature names.
    tags : list
        The list of tags.
    """
    tags = set()
    vocabulary = defaultdict(int)
    for sent in reader.sents():
        untagged_sent = [token for (token, tag) in sent]
        tag_seq = [tag for (token, tag) in sent]
        for tag in tag_seq:
            tags.add(tag)
        length = len(untagged_sent)
        for index in range(length):
            features = fd(untagged_sent, index, length)
            pre_tags = tag_seq[:index]
            history = hd(pre_tags, untagged_sent, index, length)
            features.extend(history)
            features = ("%s=%s" % (ftype, fval)
                        for ftype, fval in features if fval)
            for fx in features:
                vocabulary[fx] += 1
    vocabulary = [fx for fx, c in vocabulary.iteritems() if c > minc]
    # If extended prediction history is used add |tags| features.
    if use_eph:
        for t in tags:
            vocabulary.append("eph=%s" % t)
    vocabulary = sorted(vocabulary)
    tags = [t for t in tags]
    return vocabulary, tags


def encode_numeric(features):
    """Encodes numeric features."""
    for ftype, fval, fnum in features:
        if fnum != 0.0:
            yield ("%s=%s" % (ftype, fval), fnum)


def encode_indicator(features):
    """Encodes indicator (=binary) features."""
    for ftype, fval in features:
        if fval:
            yield ("%s=%s" % (ftype, fval), 1.0)


def asinstance(enc_features, fidx_map):
    """Convert a list of encoded features
    to the corresponding
    feature vector.

    Arguments
    ---------
    enc_features : list of encoded features
    fidx_map : dict
        A dict mapping features to feature ids.

    Returns
    -------
    array, dtype = bolt.io.sparsedtype
        The feature vector.

    """
    instance = []
    for fid, fval in enc_features:
        if fid in fidx_map:
            instance.append((fidx_map[fid], fval))
    return bolt.fromlist(instance, bolt.sparsedtype)


@timeit
def build_examples(reader, fd, hd, fidx_map, T, use_eph=False):
    tidx_map = dict([(tag, i) for i, tag in enumerate(T)])
    instances = []
    labels = []
    if use_eph:
        eph = ExtendedPredictionHistory(tidx_map)
    i = 0
    for sent in reader.sents():
        untagged_sent, tag_seq = zip(*sent)
        length = len(untagged_sent)
        for index in range(length):
            features = fd(untagged_sent, index, length)
            pre_tags = tag_seq[:index]
            tag = tag_seq[index]
            history = hd(pre_tags, untagged_sent,
                         index, length)
            features.extend(history)
            enc_features = encode_indicator(features)
            if use_eph:
                w = untagged_sent[index][0]
                if w in eph:
                    dist = eph[w]
                    dist = [("eph", T[i], v) for i, v in enumerate(dist)]
                    enc_features = chain(enc_features, encode_numeric(dist))
                if tag != "O":
                    eph.push(w, tag)

            instance = asinstance(enc_features, fidx_map)
            if tag == "Unk":
                tag = -1
            else:
                tag = tidx_map[tag]
            instances.append(instance)
            labels.append(tag)
    instances = bolt.fromlist(instances, np.object)
    labels = bolt.fromlist(labels, np.float64)
    return bolt.io.MemoryDataset(len(fidx_map), instances, labels)


class Tagger(object):
    """Tagger base class."""
    def __init__(self, fd, hd, verbose=0):
        self.fd = fd
        self.hd = hd
        self.verbose = verbose

    def tag(self, sent):
        """tag a sentence.
        :returns: a sequence of tags
        """
        pass

    def batch_tag(self, sents):
        """Tags each sentences.
        """
        i = 0
        for sent in sents:
            tagseq = [tag for tag in self.tag(sent)]
            yield tagseq
            i += 1


class GreedyTagger(Tagger):
    """Base class for Taggers with greedy left-to-right decoding.
    """

    def __init__(self, *args, **kargs):
        super(GreedyTagger, self).__init__(*args, **kargs)

    @timeit
    def feature_extraction(self, train_reader, minc=1, use_eph=False):
        """Extracts the features from the given training reader.
        Builds up various data structures such as the vocabulary and
        the tag set. Furthermore, it creates a training set from the
        given training reader.
        """
        print "------------------------------"
        print "Feature extraction".center(30)
        print "min count: ", minc
        print "use eph: ", use_eph
        self.minc = minc
        self.use_eph = use_eph
        V, T = build_vocabulary(train_reader, self.fd, self.hd, minc=minc,
                                use_eph=self.use_eph)
        self.V, self.T = V, T
        self.fidx_map = dict([(fname, i) for i, fname in enumerate(V)])
        self.tidx_map = dict([(tag, i) for i, tag in enumerate(T)])
        self.tag_map = dict([(i, t) for i, t in enumerate(T)])
        print "building examples..."
        dataset = build_examples(train_reader, self.fd, self.hd,
                                 self.fidx_map, T, use_eph=self.use_eph)
        dataset.shuffle(13)
        self.dataset = dataset
        if use_eph:
            self.eph = ExtendedPredictionHistory(self.tidx_map)

    @timeit
    def train(self, reg=0.0001, epochs=30, shuffle=False):
        dataset = self.dataset
        T = self.T
        print "------------------------------"
        print "Training".center(30)
        print "num examples: %d" % dataset.n
        print "num features: %d" % dataset.dim
        print "num classes: %d" % len(T)
        print "classes: ", T
        print "reg: %.8f" % reg
        print "epochs: %d" % epochs
        glm = bolt.GeneralizedLinearModel(dataset.dim, len(T), biasterm=True)
        self._train(glm, dataset, epochs=epochs, reg=reg, verbose=self.verbose,
                    shuffle=shuffle)
        self.glm = glm

    def _train(self, glm, dataset, **kargs):
        raise NotImplementedError

    def tag(self, sent):
        untagged_sent = [token for (token, tag) in sent]
        length = len(untagged_sent)
        tag_seq = []
        for index in range(length):
            w = untagged_sent[index][0]
            features = self.fd(untagged_sent, index, length)
            history = self.hd(tag_seq, untagged_sent, index, length)
            features.extend(history)
            enc_features = encode_indicator(features)
            if self.use_eph:
                if w in self.eph:
                    dist = self.eph[w]
                    dist = [("eph", self.T[i], v) for i, v in enumerate(dist)]
                    enc_features = chain(enc_features, encode_numeric(dist))
            instance = asinstance(enc_features, self.fidx_map)
            p = self.glm(instance)
            tag = self.tag_map[p]
            tag_seq.append(tag)
            if self.use_eph and tag != "O":
                self.eph.push(w, tag)
            yield tag_seq[-1]

    def describe(self, k=20):
        """Describes the trained model.
        """
        for i, w in enumerate(self.glm.W):
            idxs = w.argsort()
            maxidx = idxs[::-1][:k]
            print self.T[i], ": "
            print ", ".join(["<%s,%.4f>" % (self.V[idx], w[idx])
                             for idx in maxidx])


class AvgPerceptronTagger(GreedyTagger):
    """A greedy left-to-right tagger that is based on an Averaged Perceptron.
    """

    def _train(self, glm, dataset, **kargs):
        epochs = kargs["epochs"]
        trainer = bolt.trainer.avgperceptron.AveragedPerceptron(epochs=epochs)
        trainer.train(glm, dataset, shuffle=kargs["shuffle"],
                      verbose=self.verbose)


class GreedySVMTagger(GreedyTagger):
    """A greedy left-to-right tagger that is based on a one-against-all
    combination  of Support Vector Machines.
    """
    def _train(self, glm, dataset, **kargs):
        sgd = bolt.SGD(bolt.ModifiedHuber(), reg=kargs["reg"],
                       epochs=kargs["epochs"])
        trainer = bolt.OVA(sgd)
        trainer.train(glm, dataset, shuffle=kargs["shuffle"],
                      verbose=self.verbose, ncpus=4)