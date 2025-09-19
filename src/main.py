"""Main application for Smart Temple People Counter."""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TemplePeopleCounter:
    def __init__(self, camera_source=None, config_file=None):
        self.camera_source = camera_source
        self.config_file = config_file
    
    def run(self):
        print("Temple Counter running...")

def create_temple_counter(camera_source=None, config_file=None):
    return TemplePeopleCounter(camera_source, config_file)

def main():
    app = TemplePeopleCounter()
    app.run()

if __name__ == "__main__":
    main()
