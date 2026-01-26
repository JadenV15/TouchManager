"""App entry point.
Starts the main controller which takes over management of the app
"""

from touchdc.ui.view.app import App
from touchdc.controller.app import AppController

def main():
    app = App()
    cont = AppController(app)
    cont.run()
    
if __name__ == '__main__':
    main()