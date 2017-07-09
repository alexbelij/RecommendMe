import csv

ratings_filename = 'ratings.csv'
normal = 'normalizedratings.csv'
file2 = open(ratingsFileName, "rt", encoding="utf-8")
file3 = open(normal, "wt", encoding="utf-8", newline='')
rating_reader = csv.reader(file2)

rating_writer = csv.writer(file3)

file2.seek(0)
avg = [0]
for user in range(1, 672):
    total = 0
    n = 0
    for row in rating_reader:
        if str(row[0]) == str(user):
            total += float(row[2])
            n = n + 1
        else:
            break

    avg.append(total / n)

file2.seek(0)
file3.seek(0)
for user in range(1, 672):
    for row in rating_reader:
        if str(row[0]) == str(user):
            rating_writer.writerow((user, row[1], row[2], str(float(row[2]) - avg[user])))
        else:
            break
