

def print_progress_bar(percentage, mb, peers, decimals=1, length=50, fill='█', print_end="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(percentage)
    mb = f"{mb:.2f}"
    filled_length = int(length * percentage // 100.0)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\rProgress: |%s| %s%% | %s MB | %s Peers' % (bar, percent, mb, peers), end=print_end)
    # prints a new line once we're done
    if percentage > 100.0:
        print()
