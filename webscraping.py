import requests
from bs4 import BeautifulSoup

# Get the company name from the user
company = input("Enter the Company Name: ")

# Construct the Wikipedia URL
website = "https://en.wikipedia.org/wiki/"
formatted_url = website + company.replace(" ", "_")  # Replace spaces with underscores
print(f"Fetching data from: {formatted_url}")

# File to save the output
output_file = f"{company.replace(' ', '_')}_details.txt"

try:
    # Make a single GET request to fetch the content
    result = requests.get(formatted_url)
    result.raise_for_status()  # Raise an error for invalid HTTP responses

    # Parse the HTML content once
    soup = BeautifulSoup(result.text, 'lxml')

    # Open the file in write mode
    with open(output_file, 'w', encoding='utf-8') as file:
        # Extract the first three <p> elements
        paragraphs = soup.find_all('p', limit=3)  # Limit to the first 3 <p> elements
        combined_text = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

        if combined_text:
            file.write("Company Summary:\n")
            file.write(combined_text + "\n\n")
            print("\nCompany Summary saved to file.")
        else:
            file.write("Company Summary:\nNo meaningful content found in the first three paragraphs.\n\n")
            print("Could not extract meaningful content from the first three paragraphs.")

        # Extract the infobox with class 'ib-company vCard'
        infobox = soup.find('table', class_='infobox ib-company vcard')
        if infobox:
            file.write("Infobox Details:\n")
            for row in infobox.find_all('tr'):
                header = row.find('th')
                data = row.find('td')
                if header and data:
                    file.write(f"{header.text.strip()}: {data.text.strip()}\n")
            print("Infobox Details saved to file.")
        else:
            file.write("Infobox Details:\nNo infobox with class 'ib-company vCard' found.\n")
            print("Could not find an infobox with class 'ib-company vCard'.")

    print(f"\nAll data has been saved to '{output_file}'.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")