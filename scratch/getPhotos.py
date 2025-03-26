import os
import requests
from bs4 import BeautifulSoup
import pickle
import networkx
from time import sleep


# Directory to save images
SAVE_DIR = "./static/images"
os.makedirs(SAVE_DIR, exist_ok=True)


with open("teamMateGraph3.pkl", "rb") as f:
    G = pickle.load(f)


player_ids = list(G.nodes()) 
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

def download_player_photo(player_id, file_a, file_b, save_dir="./static/images"):
    # Construct the URL for the player's Basketball Reference page
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    
    try:
        sleep(3)
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the page content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the image in the media-item div
        media_item = soup.find('div', class_='media-item')
        if media_item and media_item.find('img'):
            img_tag = media_item.find('img')
            img_url = img_tag['src']
            
            # Convert relative URL to absolute URL if needed
            img_url = urljoin(url, img_url)
            
            # Download the image
            img_response = requests.get(img_url, headers=headers)
            img_response.raise_for_status()
            
            # Save the image
            save_path = os.path.join(save_dir, f"{player_id}.jpg")
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            print(f"Successfully downloaded {player_id}.jpg")
            
        else:
            pname = str(G.nodes[player_id]["name"])
            file_a.write(f"{player_id}-{pname}\n")
            print(f"No image found for player {player_id}")
            
    except requests.RequestException as e:
        pname = str(G.nodes[player_id]["name"])
        file_b.write(f"{player_id}-{pname}\n")
        print(f"Error downloading image for {player_id}: {str(e)}")

def download_multiple_players(player_ids, save_dir="./static/images"):
    with open("image_not_found.txt", "a") as file_a, open("error_downloading.txt", "a") as file_b, open("progress.txt", "w") as file_c:
        i = 0
        j = len(player_ids)
        go = False
        for player_id in player_ids:
            i += 1
            print("progress: "+str(i/j))
            if not go:
                if player_id == 'grayeje01':
                    go = True
            else:
                file_c.write(str(i/j)+"\n")
                file_path = f"static/images/{player_id}.jpg"
                if os.path.isfile(file_path):
                    print(f"Picture Exists for {player_id}")
                else:
                    download_player_photo(player_id,file_a, file_b,save_dir)

# Example usage
if __name__ == "__main__":
    download_multiple_players(player_ids)
    # Example list of player IDs (replace with your actual list)

    # Download all photos
    #download_multiple_players(player_ids)


