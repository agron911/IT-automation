def format_address(address_string):
    num = 0
    addr =''
    address = address_string.split()
    for string in address:
        if string.isnumeric():
            num+=int(string)
        else:
            addr+=string+' '
    return 'house number {} on street named {}'.format(num,addr)

print(format_address("123 Main Street"))
# Should print: "house number 123 on street named Main Street"
print(format_address("1001 1st Ave"))
# Should print: "house number 1001 on street named 1st Ave"
print(format_address("55 North Center Drive"))
# Should print "house number 55 on street named North Center Drive"
