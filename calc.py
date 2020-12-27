def show_chance(deck_size=60, num_in_deck=4, depth=30):
	i = 0
	a = 1
	while (depth > 0):
		depth -= 1
		a *= (deck_size - num_in_deck)/deck_size
		deck_size -= 1
		i += 1
		print(str(i) + ": "+"{:.2f}".format(1-a))

