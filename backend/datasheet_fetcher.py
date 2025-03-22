import requests

def fetch_datasheet(component_name):
    """ Searches for an electronics component's datasheet online. """
    search_url = f"https://www.datasheetarchive.com/{component_name}-datasheet.html"

    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            return search_url  # Return the link to the datasheet
        else:
            return "Datasheet not found."
    except Exception as e:
        return f"Error fetching datasheet: {e}"
