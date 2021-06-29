def highlight_word(sentence, word):
	# return (w.upper() if w==word else w for w in sentence.split())
	return (sentence[:sentence.index(word)]+word.upper()+sentence[sentence.index(word)+len(word):])

print(highlight_word("Have a nice day", "nice"))
print(highlight_word("Shhh, don't be so loud!", "loud"))
print(highlight_word("Automating with Python is fun", "fun"))
