def RemoveValue(myval):
    if myval not in my_list:
        raise ValueError('Value must be in the list')
    else:
        my_list.remove(myval)
    return my_list

my_list = [27, 5, 9, 6, 8]
print(RemoveValue(27))
# print(RemoveValue(27))

my_word_list = ['east', 'after', 'up', 'over', 'inside']

def OrganizeList(myList):
    for item in myList:
        if type(item) != 'str':
            raise AssertionError('Word list must be a list of strings')
    myList.sort()
    return myList
print(OrganizeList(my_word_list))

def Guess(participants):
    my_participant_dict = {}
    for participant in participants:
        my_participant_dict[participant] = random.randint(1, 9)
        print(participant,my_participant_dict[participant])
    try:
        if my_participant_dict['Larry'] == 9:
            return True
    except:
        return None

participants = ['Cathy','Fred','Jack','Larry','Tom']
print(Guess(participants))