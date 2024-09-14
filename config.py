import toml


def get_str():

    with open('/Users/doc/projects//mds/mclguide/mcl.config', "r") as f:
        config = toml.load(f)
        print(config)

    # new_toml_string['database']['level2'] = 'new added information'
    # with open('config.toml', 'w') as f:
if __name__ == '__main__':
    get_str()
