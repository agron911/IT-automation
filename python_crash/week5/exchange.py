class Person:
    apples = 0
    ideas = 0
john = Person()
john.apples=1
john.ideas=1

martin = Person()
martin.apples=2
martin.ideas=1

def exchange_apples(you, me):
    you.apples, me.apples = me.apples,you.apples
    return you.apples,me.apples

def exchange_ideas(you,me):
    you.ideas+=me.ideas
    me.ideas=you.ideas
    return you.ideas,me.ideas

exchange_apples(john, martin)
print("Johanna has {} apples and Martin has {} apples".format(john.apples, martin.apples))
exchange_ideas(john, martin)
print("Johanna has {} ideas and Martin has {} ideas".format(john.ideas, martin.ideas))
