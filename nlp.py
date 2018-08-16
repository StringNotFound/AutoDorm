objects = {'leds', 'led', 'color', 'fan', 'volume', 'light', 'lights', 'computer', 'blind', 'blinds', 'shade', 'shades', 'feeling'}
actions = {'play', 'just-play', 'red', 'orange', 'yellow', 'green', 'blue', 'dark blue', 'purple', 'pink', 'white', 'rainbow', 'off', 'on', 'high', 'low', 'medium', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'close', 'open', 'shut', 'sad', 'happy', 'romantic', 'energetic', 'epic'}
conjunctions = {'and', 'but'}
transtive_verbs = {'turn'}
article_adjs = {'the', 'a', 'an'}

# returns a list of sets, where each set is a subset of words deliminated by the occurrence of one of the
# conjunctions in words
def words2sections(words):
    sections = []
    cursec = set()
    for word in words:
        if word in conjunctions:
            sections.append(cursec)
            cursec = set()
        else:
            cursec.add(word)
    if len(cursec) > 0:
        sections.append(cursec)
    return sections


# if two objects are adjacent to each other, insert an and (remove the article_adjs first)
def insertANDS(words):
    new_words = []
    prev_word_is_object = False
    for w in words:
        if w in objects:
            if prev_word_is_object:
                new_words.append('and')
            prev_word_is_object = True
        else:
            prev_word_is_object = False
        new_words.append(w)
    return new_words

def locateObjectsActions(section):
    obj = 0
    act = 0
    for w in section:
        if w in objects:
            if obj != 0:
                raise SyntaxError('multiple objects found in section')
            obj = w
        if w in actions:
            if act != 0:
                raise SyntaxError('multiple actions found in section')
            act = w
    if obj == 0 and act == 0:
        raise SyntaxError('no objects or actions found in AND deliminated section')
    if obj == 0 and act == 1:
        raise SyntaxError('just an action found in AND deliminated section')
    return (obj, act)

"""
returns the next action in the direction given by direction starting at one off from start

returns: (index, action) or 0 if no action could be found
"""
def get_next_action(direction, objacts, start):
    i = start
    if direction == 'left':
        i -= 1
        while i >= 0:
            if objacts[i][1] != 0: return (objacts[i][1], i)
            i -= 1
    if direction == 'right':
        i += 1
        while i < len(objacts):
            if objacts[i][1] != 0: return (objacts[i][1], i)
            i += 1
    # we didn't find an action :(
    return (0, 0)

"""
parses a phrase, extracting the object/action pairs

returns: a list of (object, action) pairs. The actions may repeat, and there is no assurance
         that the objects will be valid targets for the actions

throws: SyntaxError if the command structure is invalid
"""
def parse_phrase(phrase):
    addon_commands = set()

    phrase = phrase.lower()
    phrase = phrase.replace('just play', 'just-play')

    words = phrase.split(' ')

    # special case a few commands
    if 'just-play' in words:
        idx = words.index('just-play')
        song = ' '.join(words[idx+1:])
        words = words[:idx]
        if song == '':
            raise SyntaxError('no song name given')
        addon_commands.add(('just-play', song))
    if 'play' in words:
        idx = words.index('play')
        song = ' '.join(words[idx+1:])
        words = words[:idx]
        if song == '':
            raise SyntaxError('no song name given')
        addon_commands.add(('play', song))

    # remove the article_adjs
    words = [w for w in words if w not in article_adjs]
    words = insertANDS(words)
    sections = words2sections(words)
    objacts = [locateObjectsActions(s) for s in sections]
    
    # fill the sections that contain tvs with the first action on their right (and also
    # fill the intervening sections with the same action)
    actionless_regions = [i for i in range(len(sections)) if objacts[i][1] == 0]
    for i in actionless_regions:
        # the region may have been given an action by a previous iteration of this for loop
        if objacts[i][1] != 0:
            continue

        # if the section that doesn't have an action contains a transitive_verb
        if len(sections[i] & transtive_verbs) > 0:
            (action, idx) = get_next_action('right', objacts, i)
            if action == 0:
                raise SyntaxError('could not find an action to the right of transtive region ' + str(i))
            for j in range(i, idx + 1):
                newpair = (objacts[j][0], action)
                objacts[j] = newpair

    # fill in remaining actionless sections with actions from the left
    actionless_regions = [i for i in range(len(sections)) if objacts[i][1] == 0]
    for i in actionless_regions:
        # the region may have been given an action by a previous iteration of this for loop
        if objacts[i][1] != 0:
            continue

        (action, idx) = get_next_action('left', objacts, i)
        for j in range(idx, i + 1):
            newpair = (objacts[j][0], action)
            objacts[j] = newpair

    # fill in remaining actionless sections with actions from the right
    actionless_regions = [i for i in range(len(sections)) if objacts[i][1] == 0]
    for i in actionless_regions:
        # the region may have been given an action by a previous iteration of this for loop
        if objacts[i][1] != 0:
            continue

        (action, idx) = get_next_action('right', objacts, i)
        for j in range(i, idx + 1):
            newpair = (objacts[j][0], action)
            objacts[j] = newpair

    actionless_regions = [i for i in range(len(sections)) if objacts[i][1] == 0]
    if len(actionless_regions) != 0:
        raise SyntaxError('could not assign actions to some regions')

    for cmd in addon_commands:
        objacts.append(cmd)

    return objacts

def test():
    test_phrase = "Set the color to red and turn off the lights"
    print(test_phrase)
    print(parse_phrase(test_phrase))
    test_phrase = "Turn off the computer and lights and set the color to red"
    print(test_phrase)
    print(parse_phrase(test_phrase))
    test_phrase = "Turn off the computer and turn the fan on"
    print(test_phrase)
    print(parse_phrase(test_phrase))
    test_phrase = "Turn the fan computer and lights on and turn the LEDs off"
    print(test_phrase)
    print(parse_phrase(test_phrase))
    test_phrase = "Just play music"
    print(test_phrase)
    print(parse_phrase(test_phrase))
    test_phrase = "Turn off the lights and play Hey There Cthulhu"
    print(test_phrase)
    print(parse_phrase(test_phrase))
