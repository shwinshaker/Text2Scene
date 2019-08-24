#!./env python
from tools.common import wait

class Test:
    def __init__(self):
        self.exit = False

    def __call__(self):
        for i in range(20):
            if not self.exit:
                print(i)
                wait(1)

def main():
    test = Test()
    test()

if __name__ == '__main__':
    main()
