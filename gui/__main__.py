from gui import GUI
import pygameextra as pe


def run_gui():
    gui = GUI()
    while gui.running:
        try:
            gui()
        except KeyboardInterrupt:
            gui.quit_check()


if __name__ == "__main__":
    run_gui()
    pe.pge_quit()
