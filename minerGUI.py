import PySimpleGUI as sg

def prompt_url():
    layout = [
        [sg.Text('Please enter the URL of the regulation')],
        [sg.Text('Should be in the format: ')],
        [sg.Text('https://laws-lois.justice.gc.ca/eng/regulations/ >>regulation<< /FullText.html')],
        [sg.Text('URL', size=(15, 1)), sg.InputText()],
        [sg.Text('Please choose the directory to export files to:')],
        [sg.Text('Folder Path:', size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
        [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Simple data entry window').Layout(layout)
    button, values = window.Read()
    return values


def prompt_folder():
    
    layout = [[sg.Text('Please choose the directory to export files to:')],
              [sg.Text('Folder Path:', size=(8, 1)), sg.InputText(), sg.FolderBrowse()],
              [sg.Submit()]]

    window = sg.Window('File Compare', layout)  

    event, values = window.Read()
    window.Close()
    return values[0]

