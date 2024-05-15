import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Initialize the Selenium WebDriver (assuming Chrome)
driver = webdriver.Chrome(executable_path='path_to_chromedriver')  # Replace 'path_to_chromedriver' with the actual path


# Function to get item details
def get_item_details(url):
    # Make a request to the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the first item
    item = soup.find('div', class_='prod_info')

    # Extract item name and original price
    item_name = item.find('p', class_='tx_name').text.strip()
    item_price = item.find('span', class_='tx_org').find('span', class_='tx_num').text.strip()

    # Extract the item URL and navigate to it using Selenium
    item_link = item.find('a')['href']
    full_item_link = f"https://www.oliveyoung.co.kr{item_link}"

    driver.get(full_item_link)
    time.sleep(3)  # Wait for the page to load

    # Extract 100 reviews
    reviews = []
    review_elements = driver.find_elements(By.CLASS_NAME,
                                           'review_text')  # Adjust the class name according to the actual HTML

    for review_element in review_elements[:100]:
        reviews.append(review_element.text.strip())

    return {
        'name': item_name,
        'price': item_price,
        'reviews': reviews
    }


# URL of the page to crawl
url = 'https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000100010014&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=48&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=0&aShowCnt=0&bShowCnt=0&cShowCnt=0&trackingCd=Cat100000100010014_Small&amplitudePageGubun=&t_page=&t_click=&midCategory=%EC%97%90%EC%84%BC%EC%8A%A4%2F%EC%84%B8%EB%9F%BC%2F%EC%95%B0%ED%94%8C&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd='

item_data = get_item_details(url)

print(f"Item Name: {item_data['name']}")
print(f"Original Price: {item_data['price']}")
print("Reviews:")
for review in item_data['reviews']:
    print(review)

# Close the WebDriver
driver.quit()
