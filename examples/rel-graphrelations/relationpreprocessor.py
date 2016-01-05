__author__ = 'hadyelsahar'

import os
import re
from os import path
import sys
import numpy as np
import cPickle as pickle

from nltk.tokenize import TreebankWordTokenizer

class RelationPreprocessor:
    """
    RelationPreprocessor class is the class responsible of converting the brat annotation
    files format of relation mentions into standard format to be processed by the RelationMentionVectorizer class
    with availability to save  the preprocessed dataset into a pickle file in the 'data' folder
    """
    def __init__(self, inputdir="./data"):
        """
        :param inputdir: directory where all .ann and all .txt files exists
                    - for each sentence in brat annotaiton tool there are two files .txt and .ann
        :param datadir: directory to save pickle files of containing X and y data
        :return: self
        """

        self.outlabel = "OUT"

        if inputdir is not None:
            print "reading data..."
            # S     :   dict {id:sentence}  the raw sentences
            # X: array(dict) [{id:, segments:[], segment_labels:[], ent1:int, ent2:int}]
            # y     :   the correct labels                           - shape: nnx1
            self.S, self.X, self.y = self.read_data(inputdir)
            print "done"


    def read_data(self, inputdir):
        """
        :param inputdir: directory contains brat annotation files
        Two files per sentence ending with ".txt" or ".ann"

        .txt : text file contains one sentence per files
        .ann : annotation file contains one Tag or relation per line
        for the scope of phrase extraction we wil concentrate only on lines starting with T
        which are the labeling for TAGS

        :return: (S,Xid,y)
         S     :   dict {id:sentence}  the raw sentences
         X: array(dict) [{sentence_id:, id:, segments:[], segment_labels:[], ent1:int, ent2:int}]
         y:   array containing all labels for X in order
        """

        files = os.listdir(inputdir)

        # select only files with annotation existing
        # get the basename without the file type
        # add .txt or .ann later
        file_names = [x.replace(".ann", "") for x in files if ".ann" in x]
        file_names.sort()

        # capital letters for corpus #small letters per sentence
        S = {}
        X = []
        y = []

        # for every training example
        for f in file_names:
            # try:
                print f
                # collect text sentences tokens
                fo = file("%s/%s.txt" % (inputdir, f), 'r')  # text file containing sentences
                txt = fo.read()
                fa = file("%s/%s.ann" % (inputdir, f), 'r')  # filling annotations with labels
                ann = fa.read()
                S[f] = txt

                # reading segments and their labels
                tags = self.get_segments(txt, ann)
                # reading relations and Generation training data
                rels, labels = self.get_relations(ann, tags, f)

                X += rels
                y += labels

                fo.close()
                fa.close()

        S = np.array(S)
        X = np.array(X)
        y = np.array(y)
        return S, X, y

    def get_segments(self, txt, ann):
        """
        reads annotated brat file and text file
        return array of sorted brat tags with (OUT) tags in between for untagged segments
        :param txt: string of brat .txt file
        :param ann: string of brat .ann file
        :return: array of tags in order [["T1", "Subject", "0", "8", "Michalka wonka"], .... ]
        """
        tokens, tokens_pos = self.tokenize(txt)

        # collect tags in the annotation by selecting lines only that contain tags
        tags = ann.split("\n")
        tags = [i for i in tags if re.match('^T', i)]
        tags = [t.split("\t") for t in tags]

        # split "Subject 00 45 into  ["subject", "00", "45"]
        tags = [[t[0]] + t[1].split(" ") + t[2:] for t in tags]
        tags = [t[0:2] + [int(t[2]), int(t[3])] + t[4:] for t in tags]
        # sort tags by start position

        tagged_range = np.array([range(int(t[2]), int(t[3])) for t in tags])
        tagged_range = [j for i in tagged_range for j in i]     # flatten

        for i, (start, end) in enumerate(tokens_pos):
            # if start and end of a token not in the tagged range add token to tags with out tag
            if len(set(range(start,end)) & set(tagged_range)) == 0:
                segid = "T%s" % str(len(tags)+1)
                tags.append([segid, self.outlabel, start, end, tokens[i]])

        # eg. ["T1", "Subject", "0", "8", "Michalka wonka"]
        tags = sorted(tags, key=lambda l: l[2])

        return tags

    def get_relations(self, ann, tags, f):
        """

        :param ann: text from brat .ann (annotation file)
        :param tags: tags extracted from self.get_tags method
                    ["T1", "Subject", "0", "8", "Michalka wonka"]
        :return: [{sentence_id:, id:, segments:[], segment_labels:[], ent1:int, ent2:int}], [labels]
        """

        X = []
        y = []
        # collect relations in the annotation file by selecting lines only that contain relations
        rels = ann.split("\n")
        rels = [i for i in rels if re.match('^R', i)]
        rels = [t.split("\t")[1] for t in rels]
        rels = [t.split(" ") for t in rels]

        for rel in rels:
            y.append(rel[0].strip())

            arg1 = rel[1].replace("Arg1:", "").strip()
            arg2 = rel[2].replace("Arg2:", "").strip()

            segments = [i[-1] for i in tags]
            segment_labels = [i[1] for i in tags]

            for c,t in enumerate(tags):
                if t[0] == arg1:
                    ent1 = c
                if t[0] == arg2:
                    ent2 = c
            x = {"sentence_id": f, "segments": segments, "segment_labels": segment_labels, "ent1": ent1, "ent2": ent2}
            X.append(x)

        return X, y


    def tokenize(self, text, returnids = True):
        """
        adaptation of Treebanktokenizer to allow start and end positions of each token of sentences
        :param s: seting sentence
        :param returnids: if true return a tuple of array of tokens and array of tuples containing start and
                        end positions of each tokens [tokens],ids[(start,end)])
                        eg.  sentence : "hello hi a" ["hello","hi","a"] [(0,5),(6,8),(9,10)]
        :return:
        """
        if returnids:

            tokens = TreebankWordTokenizer().tokenize(text)
            positions = []
            start = 0
            for token in tokens:
                positions.append((start, start+len(token)))
                start = start+len(token)+1

            return tokens, positions

        else:
            TreebankWordTokenizer().tokenize(s)



p = RelationPreprocessor()