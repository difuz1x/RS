

def count_avg(*args): #became cort
    return sum(args)/len(args)

print(count_avg(1,2,3,4,5))
print(count_avg(*[1,2,3,4,5,6]))
print(count_avg(*(1,2,3,4,5,6)))
print(count_avg(3))


def count_avg_2(**kwargs):
    for i, (key, values) in enumerate(kwargs.items(), start =1 ):
        print(str(i)+ " " + key + " : " + str(values))
    return sum(kwargs.values())/len(kwargs)

print (count_avg_2(math=5))
print(count_avg_2(**{"a":1, "b":2, "c":3}))