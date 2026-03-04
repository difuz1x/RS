
def get_outdated(robots: list, new_version: int) -> list:
    old_robots=[]
    for index, robot in enumerate(robots):
        if robot["core_version"]<new_version:
            old_robots.append(index)
    return old_robots


    test = [ {"core version: 9"},
            {"core version: 15"}
    
    ]

    print(get_outdated(test,10))
    