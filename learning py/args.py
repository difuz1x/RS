
def sum_dicts(*args):

    new_dict= {}
    for dictionary in args:
            for key,value in  dictionary.items():
                if key in new_dict:
                    new_dict[key] += value
                else:
                    new_dict[key]=value
    return new_dict