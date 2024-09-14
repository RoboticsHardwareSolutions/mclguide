import nc_py_api

nc = nc_py_api.Nextcloud(nextcloud_url="", nc_auth_user="a.",
                         nc_auth_pass="!")


def list_dir(directory):
    # usual recursive traversing over directories
    for node in nc.files.listdir(directory):
        if node.is_dir:
            list_dir(node)
        else:
            print(f"{node.user_path}")


if __name__ == "__main__":
    # create Nextcloud client instance class

    # list_dir("")
    # list_dir("")
    file = nc.files.download(
        ")

    with open("file.SLDPRT", "wb") as handle:
        handle.write(file)
    handle.close()

    exit(0)
