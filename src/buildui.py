import sys
import glob
import os

def main():
    args = sys.argv[1:]

    if not args:
        # build all of them
        flist = glob.glob("../ui/*.ui")
        for f in flist:
            o = "ui_"+f[6:].replace(".ui",".py") # the "6" skips over the "../ui/"
            # compare times
            go = False
            ci = os.path.getmtime(f)
            # print(f"{f} time is    {ci}")
            try:
                co = os.path.getmtime(o)
                # print(f"{o} time is {co}")
                if ci > co:
                    # print(ci,co,ci-co)
                    go = True
            except FileNotFoundError:
                go = True
            if go:
                s = f"pyside6-uic {f} -o {o}"
                print(s)
                os.system(s)
    else:
        for f in args:
            o = "ui_"+f.replace(".ui",".py")
            s = f"pyside6-uic {f} -o {o}"
            os.system(s)
            #print(s)


if __name__ == "__main__":
    main()