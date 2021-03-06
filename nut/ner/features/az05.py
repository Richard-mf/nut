"""Feature and history detectors for CoNLL03 taken from:

`Ando, R. K. and Zhang, T. (2005). A Framework for Learning Predictive
Structures from Multiple Tasks and Unlabeled Data. J. Mach. Learn. Res., 6:1817-1853.`

TODO: short description.
"""
WORD, POS, NP, LEMMA = 0, 1, 2, 3


def fd(sent, index, length):
    """Feature detector from ZJ03
    """
    context = lambda idx, field: sent[index + idx][field] \
              if index+idx >= 0 and index + idx < length \
              else "<s>" if index+idx < 0 \
              else "</s>"

    def bow(i, j):
        bows = []
        minidx = (index - i if index - i > 0 else 0)
        maxidx = (index + i if index + i < length else length)
        for w in sent[minidx:maxidx]:
            bows.append(('bow%d-%d' % (i, j), w[WORD]))

        return bows

    ## tokens in a 5 token window w_{i-2}..w_{i+2}
    w = context(0, WORD)
    pre_w = context(-1, WORD)
    pre_pre_w = context(-2, WORD)
    post_w = context(1, WORD)
    post_post_w = context(2, WORD)

    ## token bigrams in a 5 token window
    pre_pre_bigram = "/".join([pre_pre_w, pre_w])
    pre_bigram = "/".join([pre_w, w])
    post_bigram = "/".join([w, post_w])
    post_post_bigram = "/".join([post_w, post_post_w])

    ## length of w
    wlen = len(w)

    ## pos in a 5 token window
    pos = context(0, POS)
    pre_pos = context(-1, POS)
    post_pos = context(1, POS)
    pre_pre_pos = context(-2, POS)
    post_post_pos = context(2, POS)

    pre_pos_bigram = "/".join([pre_pos, pos])
    post_pos_bigram = "/".join([pos, post_pos])
    pre_pre_pos_bigram = "/".join([pre_pre_pos, pre_pos])
    post_post_pos_bigram = "/".join([post_pos, post_post_pos])
    pos_w = "/".join([w, pos])

    ## Word shape features (5 token window)
    istitle = w.istitle()
    isdigit = w.isdigit()
    isupper = w.isupper()
    isalnum = w.isalnum()
    hyphen = "-" in w[1:-1]
    is2digit = isdigit and len(w)==2
    is4digit = isdigit and len(w)==4

    pre_istitle = pre_w.istitle()
    pre_isdigit = pre_w.isdigit()
    pre_isupper = pre_w.isupper()
    pre_hyphen = "-" in pre_w[1:-1]
    pre_isalnum = pre_w.isalnum()
    pre_is2digit = pre_isdigit and len(pre_w)==2
    pre_is4digit = pre_isdigit and len(pre_w)==4

    pre_pre_istitle = pre_pre_w.istitle()
    pre_pre_isdigit = pre_pre_w.isdigit()
    pre_pre_isupper = pre_pre_w.isupper()
    pre_pre_hyphen = "-" in pre_pre_w[1:-1]
    pre_pre_isalnum = pre_pre_w.isalnum()
    pre_pre_is2digit = pre_pre_isdigit and len(pre_pre_w)==2
    pre_pre_is4digit = pre_pre_isdigit and len(pre_pre_w)==4

    post_istitle = post_w.istitle()
    post_isdigit = post_w.isdigit()
    post_isupper = post_w.isupper()
    post_hypen = "-" in post_w[1:-1]
    post_isalnum = post_w.isalnum()
    post_is2digit = post_isdigit and len(post_w)==2
    post_is4digit = post_isdigit and len(post_w)==4

    post_post_istitle = post_post_w.istitle()
    post_post_isdigit = post_post_w.isdigit()
    post_post_isupper = post_post_w.isupper()
    post_post_hypen = "-" in post_post_w[1:-1]
    post_post_isalnum = post_post_w.isalnum()
    post_post_is2digit = post_post_isdigit and len(post_post_w)==2
    post_post_is4digit = post_post_isdigit and len(post_post_w)==4

    ## 2-4 suffixes in a 4 token window
    w_suffix1 = w[-1:]
    w_suffix2 = w[-2:]
    w_suffix3 = w[-3:]
    w_suffix4 = w[-4:]

    pre_w_suffix1 = pre_w[-1:]
    pre_w_suffix2 = pre_w[-2:]
    pre_w_suffix3 = pre_w[-3:]
    pre_w_suffix4 = pre_w[-4:]

    post_w_suffix1 = post_w[-1:]
    post_w_suffix2 = post_w[-2:]
    post_w_suffix3 = post_w[-3:]
    post_w_suffix4 = post_w[-4:]

    pre_pre_w_suffix1 = pre_pre_w[-1:]
    pre_pre_w_suffix2 = pre_pre_w[-2:]
    pre_pre_w_suffix3 = pre_pre_w[-3:]
    pre_pre_w_suffix4 = pre_pre_w[-4:]

    post_post_w_suffix1 = post_post_w[-1:]
    post_post_w_suffix2 = post_post_w[-2:]
    post_post_w_suffix3 = post_post_w[-3:]
    post_post_w_suffix4 = post_post_w[-4:]

    ## 2-4 suffixes in a 4 token window
    w_suffix1 = w[:1]
    w_suffix2 = w[:2]
    w_suffix3 = w[:3]
    w_suffix4 = w[:4]

    pre_w_suffix1 = pre_w[:1]
    pre_w_suffix2 = pre_w[:2]
    pre_w_suffix3 = pre_w[:3]
    pre_w_suffix4 = pre_w[:4]

    post_w_suffix1 = post_w[:1]
    post_w_suffix2 = post_w[:2]
    post_w_suffix3 = post_w[:3]
    post_w_suffix4 = post_w[:4]

    pre_pre_w_suffix1 = pre_pre_w[:1]
    pre_pre_w_suffix2 = pre_pre_w[:2]
    pre_pre_w_suffix3 = pre_pre_w[:3]
    pre_pre_w_suffix4 = pre_pre_w[:4]

    post_post_w_suffix1 = post_post_w[:1]
    post_post_w_suffix2 = post_post_w[:2]
    post_post_w_suffix3 = post_post_w[:3]
    post_post_w_suffix4 = post_post_w[:4]

    ## Noun phrase in a 3 token window
    np = context(0,NP)
    np_w = "/".join([np, w])
    pre_np = context(-1, NP)
    post_np = context(1, NP)

    ## Extract features from local scope
    features = locals()
    del features["context"]
    del features['bow']
    del features["sent"]
    del features["index"]
    del features["length"]
    features = features.items()

    features.extend(bow(-4, -1))
    features.extend(bow(1, 4))
    
    return features


def hd_az05(tags, sent, index, length, occurrences={}):
    context = lambda idx, field: sent[index + idx][field] \
              if index+idx >= 0 and index + idx < length \
              else "<s>" if index+idx < 0 \
              else "</s>"

    pre_tag = tags[index - 1] if index - 1 >= 0 else "<s>"
    pre_pre_tag = tags[index - 2] if index - 2 >= 0 else "<s>"
    pre_tag_w = "/".join([pre_tag, context(0, WORD)])
    tag_bigram = "/".join([pre_pre_tag, pre_tag])
    
    history = [("pre_tag", pre_tag), ("pre_pre_tag", pre_pre_tag),
               ("pre_tag_w", pre_tag_w), ("tag_bigram", tag_bigram)]
    return history


