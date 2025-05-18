result = "\nGAME OVER,"
playtime: int = 23
playtime_hours: int = playtime // 3600
playtime_minutes: int = (playtime%3600) // 60
playtime_seconds: int = playtime % 60
playtime_string: str = ""
add_padding_zero = lambda number, next_one_padded: "0" + str(number) if len(str(number)) == 1 and next_one_padded else str(number)
next_one_padded: bool = False
if playtime_hours != 0:
    playtime_string += str(playtime_hours) + " hours "
    next_one_padded = True
if playtime_minutes != 0 or next_one_padded:
    playtime_string += add_padding_zero(playtime_minutes, next_one_padded) + " minutes "
    next_one_padded = True
if playtime_seconds != 0 or next_one_padded:
    playtime_string += add_padding_zero(playtime_seconds, next_one_padded) + " seconds "

result += f" PLAYTIME: {playtime_string}"

print(result)